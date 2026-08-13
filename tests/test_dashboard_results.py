"""
Tests for dashboard/results.py -- US-6.2
"""
import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard.results import (
    load_experiments_summary,
    load_predictions_summary,
    load_benchmarks_summary,
    create_ab_pvalue_chart,
    create_benchmark_chart,
)


class TestDashboardResults:
    def test_load_experiments_summary(self, mocker):
        mock_conn = mocker.MagicMock()
        mock_res = mocker.MagicMock()
        mock_res.fetchall.return_value = [
            ("Exp 1", 0.01, 0.45, True, '{"test_type": "t-test"}')
        ]
        mock_res.keys.return_value = ["name", "p_value", "effect_size", "is_significant", "summary"]
        mock_conn.execute.return_value = mock_res

        df = load_experiments_summary(mock_conn)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert df.loc[0, "name"] == "Exp 1"

    def test_load_predictions_summary(self, mocker):
        mock_conn = mocker.MagicMock()
        mock_res = mocker.MagicMock()
        mock_res.fetchall.return_value = [
            ("ds-1", "target", "regression", '{"rmse": 0.1, "r2": 0.95}', "models/m.joblib")
        ]
        mock_res.keys.return_value = ["dataset_id", "target_column", "model_type", "metrics", "model_path"]
        mock_conn.execute.return_value = mock_res

        df = load_predictions_summary(mock_conn)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_create_ab_pvalue_chart(self):
        df = pd.DataFrame({
            "name": ["Exp A", "Exp B"],
            "p_value": [0.01, 0.12],
            "is_significant": [True, False],
        })
        fig = create_ab_pvalue_chart(df)
        assert isinstance(fig, go.Figure)

    def test_create_benchmark_chart(self):
        df = pd.DataFrame({
            "query_label": ["Lookup Q1"],
            "before_ms": [20.0],
            "after_ms": [0.5],
        })
        fig = create_benchmark_chart(df)
        assert isinstance(fig, go.Figure)
