"""
Tests for dashboard/stats.py -- US-6.1
"""
import pandas as pd
import pytest

from dashboard.stats import compute_summary_stats


class TestDashboardStats:
    def test_compute_summary_stats_numeric(self):
        df = pd.DataFrame({
            "age": [20, 30, 40, None],
            "score": [1.0, 2.0, 3.0, 4.0],
        })
        stats_df = compute_summary_stats(df)
        assert isinstance(stats_df, pd.DataFrame)
        assert "column" in stats_df.columns
        assert "mean" in stats_df.columns
        assert "missing_count" in stats_df.columns

        age_row = stats_df[stats_df["column"] == "age"].iloc[0]
        assert age_row["missing_count"] == 1
        assert pytest.approx(age_row["mean"], 0.01) == 30.0

    def test_compute_summary_stats_categorical(self):
        df = pd.DataFrame({
            "group": ["A", "A", "B", None],
        })
        stats_df = compute_summary_stats(df)
        group_row = stats_df[stats_df["column"] == "group"].iloc[0]
        assert group_row["missing_count"] == 1
        assert group_row["unique_values"] == 2
