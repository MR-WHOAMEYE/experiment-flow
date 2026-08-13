"""
EaaS Platform — File Ingestor (US-1.1, US-1.3)

Responsibilities:
  - Parse CSV and Excel files into DataFrames (parse_csv, parse_excel)
  - Load rows into raw_ingest table and return a dataset_id (ingest_file)
  - Upsert rows into clean_records with de-duplication (upsert_to_clean_records)

Design:
  - IngestionError is the single domain error surfaced to callers.
  - Every public function logs start/end/row_count/error in structured JSON.
  - No DB writes occur if parsing raises — atomicity guaranteed by caller
    passing a transactional connection.

References: ADR-001 (upsert), prompt.md US-1.1, US-1.3
"""
import json
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ingestion.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Domain error
# ---------------------------------------------------------------------------

class IngestionError(Exception):
    """Raised for any recoverable ingestion failure (bad file, empty data, etc.)."""


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def parse_csv(filepath: Path) -> pd.DataFrame:
    """
    Parse a CSV file into a DataFrame.

    Args:
        filepath: Absolute or relative Path to the CSV file.

    Returns:
        A non-empty pandas DataFrame.

    Raises:
        IngestionError: If the file does not exist, is empty, has no data rows,
                        or cannot be parsed.
    """
    filepath = Path(filepath)
    log.info("parse_csv started", extra={"file": str(filepath)})

    if not filepath.exists():
        raise IngestionError(f"File not found: {filepath}")

    if filepath.stat().st_size == 0:
        raise IngestionError(f"File is empty: {filepath}")

    try:
        df = pd.read_csv(filepath)
    except Exception as exc:
        raise IngestionError(f"Failed to parse CSV '{filepath}': {exc}") from exc

    if df.empty or len(df) == 0:
        raise IngestionError(f"File has no data rows: {filepath}")

    log.info("parse_csv complete", extra={"file": str(filepath), "rows": len(df), "cols": len(df.columns)})
    return df


def parse_excel(filepath: Path) -> pd.DataFrame:
    """
    Parse an Excel (.xlsx / .xls) file into a DataFrame.

    Args:
        filepath: Absolute or relative Path to the Excel file.

    Returns:
        A non-empty pandas DataFrame.

    Raises:
        IngestionError: If the file does not exist, is empty, has no data rows,
                        or cannot be parsed.
    """
    filepath = Path(filepath)
    log.info("parse_excel started", extra={"file": str(filepath)})

    if not filepath.exists():
        raise IngestionError(f"File not found: {filepath}")

    if filepath.stat().st_size == 0:
        raise IngestionError(f"File is empty: {filepath}")

    try:
        df = pd.read_excel(filepath)
    except Exception as exc:
        raise IngestionError(f"Failed to parse Excel '{filepath}': {exc}") from exc

    if df.empty or len(df) == 0:
        raise IngestionError(f"File has no data rows: {filepath}")

    log.info("parse_excel complete", extra={"file": str(filepath), "rows": len(df), "cols": len(df.columns)})
    return df


# ---------------------------------------------------------------------------
# Main ingestion entry point
# ---------------------------------------------------------------------------

def ingest_file(
    filepath: Path,
    source_name: str,
    conn: Connection,
    dataset_id: Optional[str] = None,
) -> str:
    """
    Parse a CSV or Excel file and insert all rows into raw_ingest.

    Args:
        filepath:    Path to the file (extension determines parser).
        source_name: Human-readable name for this data source.
        conn:        A SQLAlchemy transactional Connection (caller controls commit).
        dataset_id:  Optional explicit dataset_id; auto-generated as UUID4 if None.

    Returns:
        dataset_id (str) — the identifier that groups all rows from this upload.

    Raises:
        IngestionError: If the file cannot be parsed; DB is NOT written to.
        ValueError:     If the file extension is unsupported.
    """
    filepath = Path(filepath)
    suffix = filepath.suffix.lower()

    log.info("ingest_file started", extra={"file": str(filepath), "source_name": source_name})

    # --- Parse (any exception here aborts before any DB write) ---
    if suffix == ".csv":
        df = parse_csv(filepath)
        source_type = "csv"
    elif suffix in (".xlsx", ".xls"):
        df = parse_excel(filepath)
        source_type = "excel"
    else:
        raise IngestionError(
            f"Unsupported file type '{suffix}'. Supported: .csv, .xlsx, .xls"
        )

    # --- Assign dataset_id ---
    if dataset_id is None:
        dataset_id = str(uuid.uuid4())

    # --- Bulk-insert rows into raw_ingest ---
    insert_sql = text(
        """
        INSERT INTO raw_ingest (source_type, source_name, dataset_id, payload)
        VALUES (:source_type, :source_name, :dataset_id, :payload)
        """
    )

    rows = [
        {
            "source_type": source_type,
            "source_name": source_name,
            "dataset_id": dataset_id,
            "payload": json.dumps(row, default=str),
        }
        for row in df.to_dict(orient="records")
    ]

    conn.execute(insert_sql, rows)

    log.info(
        "ingest_file complete",
        extra={"dataset_id": dataset_id, "rows_inserted": len(rows), "source_name": source_name},
    )
    return dataset_id


# ---------------------------------------------------------------------------
# Upsert into clean_records (US-1.3 — ADR-001)
# ---------------------------------------------------------------------------

def upsert_to_clean_records(
    df: pd.DataFrame,
    dataset_id: str,
    conn: Connection,
    unique_key_column: Optional[str] = None,
) -> dict:
    """
    Upsert cleaned DataFrame rows into clean_records using PostgreSQL ON CONFLICT DO UPDATE.

    Args:
        df:                 Cleaned DataFrame to persist.
        dataset_id:         Identifier for the dataset these rows belong to.
        conn:               A SQLAlchemy transactional Connection.
        unique_key_column:  Column name to use as unique_key. Defaults to the first column.

    Returns:
        dict with keys: inserted, updated (row counts are approximate — based on attempted rows).

    References:
        ADR-001: INSERT ... ON CONFLICT DO UPDATE keyed on (dataset_id, unique_key).
    """
    if unique_key_column is None:
        unique_key_column = df.columns[0]

    log.info(
        "upsert_to_clean_records started",
        extra={"dataset_id": dataset_id, "rows": len(df), "key_col": unique_key_column},
    )

    upsert_sql = text(
        """
        INSERT INTO clean_records (dataset_id, unique_key, fields)
        VALUES (:dataset_id, :unique_key, :fields)
        ON CONFLICT (dataset_id, unique_key)
        DO UPDATE SET
            fields     = EXCLUDED.fields,
            cleaned_at = now()
        """
    )

    rows = [
        {
            "dataset_id": dataset_id,
            "unique_key": str(row.get(unique_key_column, "")),
            "fields": json.dumps(row, default=str),
        }
        for row in df.to_dict(orient="records")
    ]

    conn.execute(upsert_sql, rows)

    log.info(
        "upsert_to_clean_records complete",
        extra={"dataset_id": dataset_id, "rows_upserted": len(rows)},
    )
    return {"upserted": len(rows)}
