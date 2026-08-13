"""
Tests for ml/trainer.py and ml/predictor.py -- US-5.1
"""
import os
from pathlib import Path
import pandas as pd
import pytest

from ml.trainer import train_model, ModelTrainingResult, save_prediction_metadata
from ml.predictor import predict


class TestMLTrainer:
    def test_train_regression_model(self, tmp_path):
        df = pd.DataFrame({
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "feature2": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
            "target": [3.1, 5.9, 9.2, 11.8, 15.1, 18.0, 21.2, 23.9, 27.1, 30.0],
        })

        res = train_model(
            df=df,
            target_column="target",
            model_type="regression",
            dataset_id="ds-reg-1",
            output_dir=tmp_path,
        )

        assert isinstance(res, ModelTrainingResult)
        assert res.model_type == "regression"
        assert "rmse" in res.metrics
        assert "r2" in res.metrics
        assert Path(res.model_path).exists()

    def test_train_classification_model(self, tmp_path):
        df = pd.DataFrame({
            "feature1": [1.0, 1.1, 1.2, 5.0, 5.1, 5.2, 1.0, 5.0, 1.1, 5.1],
            "target": ["A", "A", "A", "B", "B", "B", "A", "B", "A", "B"],
        })

        res = train_model(
            df=df,
            target_column="target",
            model_type="classification",
            dataset_id="ds-cls-1",
            output_dir=tmp_path,
        )

        assert isinstance(res, ModelTrainingResult)
        assert res.model_type == "classification"
        assert "accuracy" in res.metrics
        assert "f1_score" in res.metrics
        assert Path(res.model_path).exists()

    def test_predict_with_saved_model(self, tmp_path):
        df_train = pd.DataFrame({
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "target": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0],
        })

        res = train_model(
            df=df_train,
            target_column="target",
            model_type="regression",
            dataset_id="ds-pred-1",
            output_dir=tmp_path,
        )

        df_new = pd.DataFrame({"feature1": [11.0, 12.0]})
        preds = predict(model_path=res.model_path, df=df_new)
        assert len(preds) == 2
        assert preds[0] > 15.0

    def test_save_prediction_metadata_executes_insert(self, mocker, tmp_path):
        mock_conn = mocker.MagicMock()
        model_file = tmp_path / "model.joblib"
        model_file.write_text("fake model data")

        res = ModelTrainingResult(
            dataset_id="ds-1",
            target_column="target",
            model_type="regression",
            metrics={"rmse": 0.12, "r2": 0.98},
            model_path=str(model_file),
            feature_columns=["feature1"],
        )

        save_prediction_metadata(mock_conn, res)
        mock_conn.execute.assert_called_once()
        _sql, params = mock_conn.execute.call_args.args
        assert params["dataset_id"] == "ds-1"
        assert params["target_column"] == "target"
