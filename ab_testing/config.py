"""
A/B Testing Experiment Config & Validator -- US-4.1 (ADR-002)

Design:
  - ExperimentConfig is a data transfer object (DTO) defining an experiment setup.
  - validate_config() validates the config against a pandas DataFrame schema before execution.
  - ConfigValidationError is raised on any validation failure.

References: ADR-002, prompt.md US-4.1
"""
from dataclasses import dataclass
import pandas as pd

from ingestion.logger import get_logger

log = get_logger(__name__)


class ConfigValidationError(Exception):
    """Raised when an ExperimentConfig fails validation against a DataFrame."""


@dataclass
class ExperimentConfig:
    """Configuration object for a single A/B experiment."""
    dataset_id: str
    name: str
    variant_column: str
    metric_column: str
    metric_type: str  # "numeric" | "categorical"


def validate_config(config: ExperimentConfig, df: pd.DataFrame) -> bool:
    """
    Validate an ExperimentConfig against a DataFrame schema.

    Args:
        config: ExperimentConfig instance.
        df:     DataFrame representing clean_records data.

    Returns:
        True if valid.

    Raises:
        ConfigValidationError: If any validation rule fails.
    """
    log.info("validate_config started", extra={"config_name": config.name})

    if config.metric_type not in ("numeric", "categorical"):
        raise ConfigValidationError(
            f"metric_type must be 'numeric' or 'categorical', got '{config.metric_type}'"
        )

    if config.variant_column not in df.columns:
        raise ConfigValidationError(
            f"variant_column '{config.variant_column}' not found in dataset columns: {list(df.columns)}"
        )

    if config.metric_column not in df.columns:
        raise ConfigValidationError(
            f"metric_column '{config.metric_column}' not found in dataset columns: {list(df.columns)}"
        )

    distinct_variants = df[config.variant_column].dropna().nunique()
    if distinct_variants < 2:
        raise ConfigValidationError(
            f"variant_column '{config.variant_column}' must have at least 2 distinct groups, got {distinct_variants}"
        )

    log.info("validate_config passed", extra={"config_name": config.name})
    return True
