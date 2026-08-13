"""
Automated End-to-End Pipeline Runner -- US-7.1

Executes the full pipeline sequentially:
  1. Ingest raw CSV/Excel file -> raw_ingest table
  2. Clean dataset -> deduplicate, strip HTML/emoji, handle missing values
  3. Upsert clean data -> clean_records table
  4. Run A/B experiment evaluation -> experiments table
  5. Train/retrain ML prediction model -> predictions table + models/ artifact
"""
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from sqlalchemy.engine import Connection

from db.connection import get_connection
from ingestion.file_ingestor import ingest_file, upsert_to_clean_records
from cleaning.cleaner import clean
from ab_testing.config import ExperimentConfig
from ab_testing.engine import evaluate_experiment, save_experiment_result
from ml.trainer import train_model, save_prediction_metadata
from ingestion.logger import get_logger

log = get_logger(__name__)


def run_end_to_end_pipeline(
    filepath: Path | str,
    source_name: str,
    conn: Connection,
    variant_column: Optional[str] = None,
    metric_column: Optional[str] = None,
    metric_type: str = "numeric",
    target_column: Optional[str] = None,
    model_type: str = "regression",
    models_dir: Path | str = "models",
) -> Dict[str, Any]:
    """
    Run full end-to-end automated pipeline.

    Returns:
        Summary dict containing dataset_id, row counts, experiment, and ML training results.
    """
    log.info("run_end_to_end_pipeline started", extra={"file": str(filepath), "source": source_name})
    filepath = Path(filepath)

    # 1. Ingestion
    dataset_id = ingest_file(filepath=filepath, source_name=source_name, conn=conn)

    # 2. Parse & Clean
    if filepath.suffix.lower() == ".csv":
        df_raw = pd.read_csv(filepath)
    else:
        df_raw = pd.read_excel(filepath)

    df_cleaned, report = clean(df_raw)

    # 3. Upsert
    upsert_res = upsert_to_clean_records(df=df_cleaned, dataset_id=dataset_id, conn=conn)

    summary: Dict[str, Any] = {
        "dataset_id": dataset_id,
        "rows_ingested": len(df_raw),
        "rows_cleaned": len(df_cleaned),
        "cleaning_report": report,
        "upserted": upsert_res["upserted"],
    }

    # 4. Optional A/B Experiment
    if variant_column and metric_column and variant_column in df_cleaned.columns and metric_column in df_cleaned.columns:
        exp_cfg = ExperimentConfig(
            dataset_id=dataset_id,
            name=f"Automated Exp - {source_name}",
            variant_column=variant_column,
            metric_column=metric_column,
            metric_type=metric_type,
        )
        exp_res = evaluate_experiment(exp_cfg, df_cleaned)
        save_experiment_result(conn, exp_res)
        summary["experiment_result"] = exp_res

    # 5. Optional ML Model Training
    if target_column and target_column in df_cleaned.columns:
        ml_res = train_model(
            df=df_cleaned,
            target_column=target_column,
            model_type=model_type,
            dataset_id=dataset_id,
            output_dir=models_dir,
        )
        save_prediction_metadata(conn, ml_res, row_count=len(df_cleaned))
        summary["ml_result"] = ml_res

    log.info("run_end_to_end_pipeline complete", extra={"dataset_id": dataset_id})
    return summary


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        with get_connection() as connection:
            res = run_end_to_end_pipeline(filepath=target_file, source_name="CLI Cron Trigger", conn=connection)
            print(f"Pipeline executed successfully for dataset_id: {res['dataset_id']}")
