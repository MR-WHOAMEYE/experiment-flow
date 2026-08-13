"""
Auto-Retraining Module -- US-5.2

Triggers model retraining when dataset row count increases.
"""
import json
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ml.trainer import train_model, save_prediction_metadata, ModelTrainingResult
from ingestion.logger import get_logger

log = get_logger(__name__)


def auto_retrain_if_needed(
    conn: Connection,
    dataset_id: str,
    df_current: pd.DataFrame,
    output_dir: Path | str = "models",
) -> Optional[ModelTrainingResult]:
    """
    Check if dataset has new rows compared to predictions table metadata; trigger retraining if so.

    Args:
        conn:       Active SQLAlchemy Connection.
        dataset_id: Dataset identifier.
        df_current: Latest cleaned DataFrame.
        output_dir: Output directory for model artifacts.

    Returns:
        ModelTrainingResult if retrained, None if skipped.
    """
    log.info("auto_retrain_if_needed started", extra={"dataset_id": dataset_id})

    # Fetch latest prediction record for dataset_id
    query_sql = text(
        """
        SELECT dataset_id, target_column, model_type, metrics
        FROM predictions
        WHERE dataset_id = :ds
        ORDER BY trained_at DESC
        LIMIT 1
        """
    )
    res = conn.execute(query_sql, {"ds": dataset_id}).fetchone()

    if not res:
        log.info("No prior training record found for dataset -- skipping auto-retrain", extra={"dataset_id": dataset_id})
        return None

    _ds_id, target_col, model_type, metrics_raw = res
    metrics = json.loads(metrics_raw) if isinstance(metrics_raw, str) else (metrics_raw or {})
    prev_row_count = metrics.get("row_count", 0)

    current_row_count = len(df_current)
    if current_row_count <= prev_row_count:
        log.info("No new rows detected -- auto-retrain skipped", extra={"current": current_row_count, "prev": prev_row_count})
        return None

    log.info(
        "New rows detected! Triggering auto-retrain...",
        extra={"current": current_row_count, "prev": prev_row_count},
    )

    retrained_result = train_model(
        df=df_current,
        target_column=target_col,
        model_type=model_type,
        dataset_id=dataset_id,
        output_dir=output_dir,
    )

    save_prediction_metadata(conn, retrained_result, row_count=current_row_count)
    return retrained_result
