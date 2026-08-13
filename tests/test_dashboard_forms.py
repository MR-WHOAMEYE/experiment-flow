"""
Tests for dashboard interactive forms -- US-8.1
"""
import pandas as pd
import pytest

from ab_testing.config import ExperimentConfig
from ab_testing.engine import evaluate_experiment


class TestDashboardForms:
    def test_interactive_experiment_creation(self):
        df = pd.DataFrame({
            "variant": ["Control", "Control", "Treatment", "Treatment"],
            "metric": [10.0, 12.0, 20.0, 22.0],
        })
        cfg = ExperimentConfig(
            dataset_id="ds-form-1",
            name="Form Created Exp",
            variant_column="variant",
            metric_column="metric",
            metric_type="numeric",
        )
        res = evaluate_experiment(cfg, df)
        assert res.p_value < 0.05
        assert res.is_significant is True
