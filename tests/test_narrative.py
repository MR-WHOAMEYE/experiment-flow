"""
Tests for dashboard/narrative.py -- US-8.2
"""
import pytest

from dashboard.narrative import generate_ab_narrative, generate_ml_narrative


class TestNarrativeGeneration:
    def test_generate_ab_narrative_significant(self):
        summary_stats = {"group_A_mean": 10.0, "group_B_mean": 12.5, "mean_difference": 2.5}
        text = generate_ab_narrative(
            experiment_name="Header Test",
            variant_col="group",
            metric_col="revenue",
            p_value=0.012,
            is_significant=True,
            effect_size=0.65,
            test_type="t-test",
            summary_stats=summary_stats,
        )
        assert "statistically significant" in text.lower()
        assert "header test" in text.lower()
        assert "0.012" in text

    def test_generate_ab_narrative_not_significant(self):
        summary_stats = {"group_A_mean": 10.0, "group_B_mean": 10.1, "mean_difference": 0.1}
        text = generate_ab_narrative(
            experiment_name="Button Color",
            variant_col="color",
            metric_col="clicks",
            p_value=0.45,
            is_significant=False,
            effect_size=0.05,
            test_type="t-test",
            summary_stats=summary_stats,
        )
        assert "not statistically significant" in text.lower()
        assert "0.45" in text

    def test_generate_ml_narrative_regression(self):
        text = generate_ml_narrative(
            target_col="price",
            model_type="regression",
            metrics={"rmse": 4.5, "r2": 0.89},
        )
        assert "regression" in text.lower()
        assert "price" in text.lower()
        assert "0.89" in text

    def test_generate_ml_narrative_classification(self):
        text = generate_ml_narrative(
            target_col="churn",
            model_type="classification",
            metrics={"accuracy": 0.92, "f1_score": 0.91},
        )
        assert "classification" in text.lower()
        assert "churn" in text.lower()
        assert "92" in text
