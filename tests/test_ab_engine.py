"""
Tests for ab_testing/engine.py -- US-4.2 (ADR-002)
"""
import numpy as np
import pandas as pd
import pytest

from ab_testing.config import ExperimentConfig
from ab_testing.engine import evaluate_experiment, save_experiment_result, ExperimentResult


class TestABTestingEngine:
    def test_numeric_experiment_ttest(self):
        """Numeric metric -> Welch's t-test, p-value, Cohen's d, CI, significance."""
        np.random.seed(42)
        group_a = np.random.normal(loc=10.0, scale=2.0, size=100)
        group_b = np.random.normal(loc=12.0, scale=2.0, size=100)

        df = pd.DataFrame({
            "variant": ["A"] * 100 + ["B"] * 100,
            "revenue": np.concatenate([group_a, group_b]),
        })

        cfg = ExperimentConfig(
            dataset_id="ds-numeric",
            name="Pricing Experiment",
            variant_column="variant",
            metric_column="revenue",
            metric_type="numeric",
        )

        res = evaluate_experiment(cfg, df)

        assert isinstance(res, ExperimentResult)
        assert res.test_type == "t-test"
        assert res.p_value < 0.05
        assert res.is_significant is True
        assert res.effect_size > 0.5  # Large Cohen's d
        assert len(res.confidence_interval) == 2

    def test_categorical_experiment_chisquare(self):
        """Categorical metric -> Chi-square test, Cram?r's V, significance."""
        df = pd.DataFrame({
            "variant": ["A"] * 100 + ["B"] * 100,
            "converted": ["Yes"] * 20 + ["No"] * 80 + ["Yes"] * 50 + ["No"] * 50,
        })

        cfg = ExperimentConfig(
            dataset_id="ds-cat",
            name="Conversion Test",
            variant_column="variant",
            metric_column="converted",
            metric_type="categorical",
        )

        res = evaluate_experiment(cfg, df)

        assert isinstance(res, ExperimentResult)
        assert res.test_type == "chi-square"
        assert res.p_value < 0.05
        assert res.is_significant is True
        assert res.effect_size > 0.1  # Cram?r's V > 0

    def test_save_experiment_result_executes_insert(self, mocker):
        mock_conn = mocker.MagicMock()
        cfg = ExperimentConfig(
            dataset_id="ds-1",
            name="Test Exp",
            variant_column="group",
            metric_column="score",
            metric_type="numeric",
        )
        res = ExperimentResult(
            config=cfg,
            test_type="t-test",
            stat_value=3.45,
            p_value=0.001,
            is_significant=True,
            effect_size=0.68,
            confidence_interval=(-3.2, -1.1),
            summary_stats={"group_A_mean": 10.0, "group_B_mean": 12.1},
        )

        save_experiment_result(mock_conn, res)
        mock_conn.execute.assert_called_once()
        _sql, params = mock_conn.execute.call_args.args
        assert params["name"] == "Test Exp"
        assert params["p_value"] == 0.001
        assert params["is_significant"] is True
