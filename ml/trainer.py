"""
ML Model Trainer -- US-5.1

Responsibilities:
  1. Train scikit-learn Regression (RandomForestRegressor) or Classification (RandomForestClassifier) models on user-selected target columns.
  2. Compute evaluation metrics:
     - Regression: RMSE (Root Mean Squared Error), R2 score
     - Classification: Accuracy, F1 score (macro)
  3. Serialize model artifacts to disk (`models/` directory or custom output_dir).
  4. Record metadata in `predictions` database table.

References: prompt.md US-5.1
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sqlalchemy import text
from sqlalchemy.engine import Connection

from ingestion.logger import get_logger

log = get_logger(__name__)


@dataclass
class ModelTrainingResult:
    """Outcome container for model training."""
    dataset_id: str
    target_column: str
    model_type: str                  # "regression" | "classification"
    metrics: Dict[str, float]
    model_path: str
    feature_columns: List[str]


def train_model(
    df: pd.DataFrame,
    target_column: str,
    model_type: str,
    dataset_id: str,
    output_dir: Path | str = "models",
) -> ModelTrainingResult:
    """
    Train a scikit-learn ML model on a cleaned DataFrame.

    Args:
        df:            Cleaned input DataFrame.
        target_column: Column name to predict.
        model_type:    "regression" or "classification".
        dataset_id:    Dataset identifier.
        output_dir:    Directory path where .joblib model file will be saved.

    Returns:
        ModelTrainingResult instance.
    """
    log.info("train_model started", extra={"dataset_id": dataset_id, "target": target_column, "type": model_type})

    if target_column not in df.columns:
        raise ValueError(f"target_column '{target_column}' not found in dataset columns: {list(df.columns)}")

    # 1. Feature selection (all numeric/categorical columns except target)
    X = df.drop(columns=[target_column])
    y = df[target_column]

    # Preprocess non-numeric features using one-hot encoding or numeric coercion
    X = pd.get_dummies(X, drop_first=True)

    # 2. Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Model training & metric computation
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if model_type == "regression":
        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mse = float(mean_squared_error(y_test, y_pred))
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_test, y_pred)) if len(y_test) > 1 else 1.0
        metrics = {"rmse": rmse, "r2": r2}

    elif model_type == "classification":
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = float(accuracy_score(y_test, y_pred))
        f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
        metrics = {"accuracy": acc, "f1_score": f1}
    else:
        raise ValueError(f"Unsupported model_type '{model_type}'. Expected 'regression' or 'classification'.")

    # 4. Serialize model artifact
    model_filename = f"{dataset_id}_{target_column}_{model_type}.joblib"
    model_path = output_dir / model_filename
    joblib.dump({"model": model, "feature_columns": list(X.columns)}, model_path)

    res = ModelTrainingResult(
        dataset_id=dataset_id,
        target_column=target_column,
        model_type=model_type,
        metrics=metrics,
        model_path=str(model_path),
        feature_columns=list(X.columns),
    )

    log.info("train_model complete", extra={"model_path": str(model_path), "metrics": metrics})
    return res


def save_prediction_metadata(conn: Connection, result: ModelTrainingResult, row_count: int = 0) -> None:
    """
    Save model training metadata into predictions database table.

    Args:
        conn:      Active SQLAlchemy Connection.
        result:    ModelTrainingResult object.
        row_count: Number of dataset rows used during training.
    """
    insert_sql = text(
        """
        INSERT INTO predictions (
            dataset_id, target_column, model_type, metrics, model_path
        ) VALUES (
            :dataset_id, :target_column, :model_type, :metrics, :model_path
        )
        """
    )

    metrics_payload = {
        **result.metrics,
        "feature_columns": result.feature_columns,
        "row_count": row_count,
    }

    conn.execute(
        insert_sql,
        {
            "dataset_id": result.dataset_id,
            "target_column": result.target_column,
            "model_type": result.model_type,
            "metrics": json.dumps(metrics_payload),
            "model_path": result.model_path,
        },
    )
    log.info("save_prediction_metadata stored in DB", extra={"dataset_id": result.dataset_id})
