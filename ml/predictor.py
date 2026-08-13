"""
ML Predictor Module -- US-5.1
"""
from pathlib import Path
import joblib
import pandas as pd

from ingestion.logger import get_logger

log = get_logger(__name__)


def predict(model_path: str | Path, df: pd.DataFrame) -> list:
    """
    Load saved model artifact and run inference on input DataFrame.

    Args:
        model_path: Path to serialized .joblib model file.
        df:         DataFrame with feature columns.

    Returns:
        List of predictions.
    """
    log.info("ml.predictor.predict started", extra={"model_path": str(model_path)})
    artifact = joblib.load(model_path)
    model = artifact["model"]
    feature_columns = artifact["feature_columns"]

    # Align input features
    df_features = pd.get_dummies(df, drop_first=True)
    for col in feature_columns:
        if col not in df_features.columns:
            df_features[col] = 0
    df_features = df_features[feature_columns]

    preds = model.predict(df_features)
    log.info("ml.predictor.predict complete", extra={"count": len(preds)})
    return preds.tolist()
