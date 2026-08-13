"""
EaaS Platform -- Automatic Data Cleaner (US-2.1)

Responsibilities:
  1. Remove exact duplicate rows.
  2. Strip HTML tags and emoji from string columns.
  3. Drop columns with >50% missing values.
  4. Impute remaining missing values:
     - Numeric: median
     - Categorical (object): mode (most frequent)
  5. Return cleaned DataFrame + CleaningReport (structured audit trail).

Design:
  - clean() is pure and stateless: same input always yields same output.
  - CleaningReport is a dataclass so callers can log or persist it.
  - No external API calls, no DB writes -- this is a transformation layer only.

References: prompt.md US-2.1
"""
import re
from dataclasses import dataclass, field
from typing import Tuple

import pandas as pd

from ingestion.logger import get_logger

log = get_logger(__name__)

# Emoji regex (covers Unicode emoji block ranges used in production)
_EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F300-\U0001F5FF"  # Misc symbols
    "\U0001F680-\U0001F6FF"  # Transport
    "\U0001F700-\U0001F77F"  # Alchemical
    "\U0001F780-\U0001F7FF"  # Geometric
    "\U0001F800-\U0001F8FF"  # Supplemental arrows
    "\U0001F900-\U0001F9FF"  # Supplemental symbols
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

_HTML_RE = re.compile(r"<[^>]+>")


@dataclass
class CleaningReport:
    """Structured audit trail for a single clean() call."""
    rows_in: int = 0
    rows_out: int = 0
    duplicates_removed: int = 0
    html_stripped: int = 0          # Number of cells modified
    emoji_stripped: int = 0         # Number of cells modified
    missing_imputed: int = 0        # Number of cells filled
    columns_dropped: int = 0        # Number of columns dropped (>50% missing)
    columns_dropped_names: list = field(default_factory=list)


def _strip_html_and_emoji(df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Strip HTML tags and emoji from all object columns in-place."""
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        original = df[col].copy()

        df[col] = df[col].apply(
            lambda v: _HTML_RE.sub("", str(v)) if isinstance(v, str) else v
        )
        html_hits = (df[col] != original).sum()
        report.html_stripped += int(html_hits)

        before_emoji = df[col].copy()
        df[col] = df[col].apply(
            lambda v: _EMOJI_RE.sub("", v) if isinstance(v, str) else v
        )
        emoji_hits = (df[col] != before_emoji).sum()
        report.emoji_stripped += int(emoji_hits)

    return df


def _handle_missing(df: pd.DataFrame, report: CleaningReport) -> pd.DataFrame:
    """Drop high-sparsity columns, impute the rest."""
    df = df.copy()
    n = len(df)

    # 1. Drop columns with >50% missing
    threshold = 0.5
    for col in df.columns:
        missing_frac = df[col].isna().mean()
        if missing_frac > threshold:
            report.columns_dropped += 1
            report.columns_dropped_names.append(col)
            df = df.drop(columns=[col])

    # 2. Impute remaining
    for col in df.columns:
        missing_count = int(df[col].isna().sum())
        if missing_count == 0:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            fill_val = df[col].median()
        else:
            mode_vals = df[col].mode()
            fill_val = mode_vals.iloc[0] if not mode_vals.empty else ""

        df[col] = df[col].fillna(fill_val)
        report.missing_imputed += missing_count

    return df


def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, CleaningReport]:
    """
    Clean a raw DataFrame and return (cleaned_df, CleaningReport).

    Pipeline (in order):
      1. Remove exact duplicate rows
      2. Strip HTML + emoji from string columns
      3. Drop >50%-missing columns, then impute remaining missing values

    Args:
        df: Raw DataFrame as loaded by the ingestion layer.

    Returns:
        Tuple of (cleaned DataFrame, CleaningReport).
    """
    report = CleaningReport(rows_in=len(df))
    log.info("cleaner.clean started", extra={"rows_in": len(df), "cols": len(df.columns)})

    # Step 1: Deduplicate
    before_dedup = len(df)
    df = df.drop_duplicates()
    report.duplicates_removed = before_dedup - len(df)

    # Step 2: HTML + emoji
    df = _strip_html_and_emoji(df, report)

    # Step 3: Missing values
    df = _handle_missing(df, report)

    # Reset index for clean downstream indexing
    df = df.reset_index(drop=True)

    report.rows_out = len(df)
    log.info(
        "cleaner.clean complete",
        extra={
            "rows_out": report.rows_out,
            "duplicates_removed": report.duplicates_removed,
            "html_stripped": report.html_stripped,
            "missing_imputed": report.missing_imputed,
            "columns_dropped": report.columns_dropped,
        },
    )
    return df, report
