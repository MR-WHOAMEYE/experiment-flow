"""
Tests for cleaning/cleaner.py -- US-2.1

Gherkin ACs:
  Given raw data contains duplicates, HTML tags, and missing values
  When the cleaning stage runs
  Then duplicates are removed, HTML/emoji are stripped, and missing values are handled
  And a cleaning report (rows affected, by type) is logged
"""
import pandas as pd
import pytest

from cleaning.cleaner import clean, CleaningReport


class TestDuplicateRemoval:
    def test_removes_exact_duplicate_rows(self):
        df = pd.DataFrame({"id": [1, 1, 2], "val": ["a", "a", "b"]})
        result, report = clean(df)
        assert len(result) == 2
        assert report.duplicates_removed == 1

    def test_no_duplicates_unchanged(self):
        df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
        result, report = clean(df)
        assert len(result) == 3
        assert report.duplicates_removed == 0


class TestHtmlEmojiStripping:
    def test_strips_html_tags(self):
        df = pd.DataFrame({"name": ["<b>Alice</b>", "<i>Bob</i>"]})
        result, report = clean(df)
        assert result["name"].tolist() == ["Alice", "Bob"]
        assert report.html_stripped > 0

    def test_strips_emojis(self):
        df = pd.DataFrame({"msg": ["Hello World", "Hi there"]})
        result, report = clean(df)
        assert "" not in result["msg"].tolist()

    def test_non_string_columns_untouched(self):
        df = pd.DataFrame({"id": [1, 2], "score": [3.14, 2.71]})
        result, report = clean(df)
        assert result["score"].tolist() == [3.14, 2.71]


class TestMissingValueHandling:
    def test_drops_column_over_50pct_missing(self):
        """Column with >50% nulls is dropped."""
        df = pd.DataFrame({"id": [1, 2, 3, 4], "sparse": [None, None, None, 1.0]})
        result, report = clean(df)
        assert "sparse" not in result.columns
        assert report.columns_dropped >= 1

    def test_imputes_numeric_column_with_median(self):
        """Numeric column with <=50% nulls: nulls filled with median."""
        df = pd.DataFrame({"id": [1, 2, 3, 4], "score": [10.0, None, 20.0, 30.0]})
        result, report = clean(df)
        assert result["score"].isna().sum() == 0
        assert result.loc[1, "score"] == pytest.approx(20.0)  # median of [10,20,30]

    def test_imputes_categorical_column_with_mode(self):
        """String column with <=50% nulls: nulls filled with mode (most frequent value)."""
        # Unique IDs ensure no rows are dropped by deduplication; 'A' appears 3x so mode is 'A'
        df = pd.DataFrame({"id": [1, 2, 3, 4, 5], "cat": ["A", "A", "A", None, "B"]})
        result, report = clean(df)
        assert result["cat"].isna().sum() == 0
        # The null at index 3 should be filled with "A" (mode)
        assert result.loc[3, "cat"] == "A"

    def test_no_missing_values_unchanged(self):
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        result, report = clean(df)
        assert result.isna().sum().sum() == 0


class TestCleaningReport:
    def test_report_has_all_fields(self):
        df = pd.DataFrame({"x": [1, 1, None], "tag": ["<b>hi</b>", "ok", "ok"]})
        _, report = clean(df)
        assert hasattr(report, "duplicates_removed")
        assert hasattr(report, "html_stripped")
        assert hasattr(report, "missing_imputed")
        assert hasattr(report, "columns_dropped")
        assert hasattr(report, "rows_in")
        assert hasattr(report, "rows_out")

    def test_rows_in_and_out_correct(self):
        df = pd.DataFrame({"id": [1, 1, 2], "val": ["a", "a", "b"]})
        _, report = clean(df)
        assert report.rows_in == 3
        assert report.rows_out == 2
