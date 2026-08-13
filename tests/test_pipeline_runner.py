"""
Tests for scripts/run_pipeline.py -- US-7.1
"""
import pandas as pd
import pytest

from scripts.run_pipeline import run_end_to_end_pipeline


class TestPipelineRunner:
    def test_run_end_to_end_pipeline(self, tmp_path, mocker):
        # Create temporary CSV file
        csv_path = tmp_path / "test_data.csv"
        csv_path.write_text("id,val,group,metric\n1,a,A,10.0\n2,b,B,15.0\n3,c,A,12.0\n4,d,B,18.0\n")

        mock_conn = mocker.MagicMock()
        # Mock database selects for predictions/records
        mock_res = mocker.MagicMock()
        mock_res.fetchone.return_value = None
        mock_conn.execute.return_value = mock_res

        summary = run_end_to_end_pipeline(
            filepath=csv_path,
            source_name="Test CSV Source",
            conn=mock_conn,
            variant_column="group",
            metric_column="metric",
            metric_type="numeric",
            target_column="metric",
            model_type="regression",
            models_dir=tmp_path / "models",
        )

        assert isinstance(summary, dict)
        assert "dataset_id" in summary
        assert summary["rows_ingested"] == 4
        assert summary["rows_cleaned"] == 4
        assert "experiment_result" in summary
        assert "ml_result" in summary
