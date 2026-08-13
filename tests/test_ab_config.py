"""
Tests for ab_testing/config.py -- US-4.1 (ADR-002)
"""
import pandas as pd
import pytest

from ab_testing.config import ExperimentConfig, ConfigValidationError, validate_config


class TestExperimentConfigValidation:
    def test_valid_config_passes(self):
        df = pd.DataFrame({"group": ["A", "B"], "revenue": [10.0, 15.0]})
        cfg = ExperimentConfig(
            dataset_id="ds-1",
            name="Revenue Test",
            variant_column="group",
            metric_column="revenue",
            metric_type="numeric",
        )
        assert validate_config(cfg, df) is True

    def test_missing_variant_column_raises_error(self):
        df = pd.DataFrame({"other": [1, 2], "revenue": [10.0, 15.0]})
        cfg = ExperimentConfig(
            dataset_id="ds-1",
            name="Revenue Test",
            variant_column="group",
            metric_column="revenue",
            metric_type="numeric",
        )
        with pytest.raises(ConfigValidationError, match="variant_column 'group' not found"):
            validate_config(cfg, df)

    def test_missing_metric_column_raises_error(self):
        df = pd.DataFrame({"group": ["A", "B"], "other": [10.0, 15.0]})
        cfg = ExperimentConfig(
            dataset_id="ds-1",
            name="Revenue Test",
            variant_column="group",
            metric_column="revenue",
            metric_type="numeric",
        )
        with pytest.raises(ConfigValidationError, match="metric_column 'revenue' not found"):
            validate_config(cfg, df)

    def test_invalid_metric_type_raises_error(self):
        df = pd.DataFrame({"group": ["A", "B"], "revenue": [10.0, 15.0]})
        cfg = ExperimentConfig(
            dataset_id="ds-1",
            name="Revenue Test",
            variant_column="group",
            metric_column="revenue",
            metric_type="unsupported_type",
        )
        with pytest.raises(ConfigValidationError, match="metric_type must be 'numeric' or 'categorical'"):
            validate_config(cfg, df)

    def test_variant_column_fewer_than_2_groups_raises_error(self):
        df = pd.DataFrame({"group": ["A", "A", "A"], "revenue": [10.0, 15.0, 20.0]})
        cfg = ExperimentConfig(
            dataset_id="ds-1",
            name="Revenue Test",
            variant_column="group",
            metric_column="revenue",
            metric_type="numeric",
        )
        with pytest.raises(ConfigValidationError, match="at least 2 distinct groups"):
            validate_config(cfg, df)
