"""
Tests for ml/retrainer.py -- US-5.2
"""
import pandas as pd
import pytest

from ml.trainer import ModelTrainingResult
from ml.retrainer import auto_retrain_if_needed


class TestMLRetrainer:
    def test_auto_retrain_triggers_when_row_count_increases(self, mocker, tmp_path):
        df_new = pd.DataFrame({
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0],
            "target": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0],
        })

        mock_conn = mocker.MagicMock()

        # Existing metadata in predictions table (10 rows previously trained)
        mock_res = mocker.MagicMock()
        mock_res.fetchone.return_value = ("ds-1", "target", "regression", '{"row_count": 10}')
        mock_conn.execute.return_value = mock_res

        retrained_res = auto_retrain_if_needed(
            conn=mock_conn,
            dataset_id="ds-1",
            df_current=df_new,
            output_dir=tmp_path,
        )

        assert retrained_res is not None
        assert isinstance(retrained_res, ModelTrainingResult)
        assert retrained_res.dataset_id == "ds-1"

    def test_auto_retrain_skips_when_no_new_rows(self, mocker, tmp_path):
        df_same = pd.DataFrame({
            "feature1": [1.0, 2.0],
            "target": [2.0, 4.0],
        })

        mock_conn = mocker.MagicMock()
        mock_res = mocker.MagicMock()
        mock_res.fetchone.return_value = ("ds-1", "target", "regression", '{"row_count": 2}')
        mock_conn.execute.return_value = mock_res

        retrained_res = auto_retrain_if_needed(
            conn=mock_conn,
            dataset_id="ds-1",
            df_current=df_same,
            output_dir=tmp_path,
        )

        assert retrained_res is None
