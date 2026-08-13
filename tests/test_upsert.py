"""
Tests for upsert_to_clean_records — US-1.3

Gherkin ACs covered:
  Given a dataset already has records with unique_key X
  When a new file containing key X is uploaded again
  Then the existing record is updated, not duplicated
  And genuinely new keys are inserted as new rows
"""
import json
from unittest.mock import MagicMock, call

import pandas as pd
import pytest

from ingestion.file_ingestor import upsert_to_clean_records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_conn(mocker) -> MagicMock:
    conn = mocker.MagicMock()
    conn.execute.return_value = mocker.MagicMock()
    return conn


# ---------------------------------------------------------------------------
# upsert_to_clean_records tests
# ---------------------------------------------------------------------------

class TestUpsertToCleanRecords:
    DATASET_ID = "dataset-abc-123"

    def test_execute_called_once(self, mocker):
        """Single batch upsert: conn.execute called exactly once."""
        conn = _make_conn(mocker)
        df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
        upsert_to_clean_records(df, self.DATASET_ID, conn, unique_key_column="id")
        conn.execute.assert_called_once()

    def test_correct_number_of_rows_passed(self, mocker):
        """The rows list passed to conn.execute must match the DataFrame length."""
        conn = _make_conn(mocker)
        df = pd.DataFrame({"id": [10, 20, 30], "score": [1.1, 2.2, 3.3]})
        upsert_to_clean_records(df, self.DATASET_ID, conn, unique_key_column="id")
        _sql, rows = conn.execute.call_args.args
        assert len(rows) == 3

    def test_unique_key_set_from_specified_column(self, mocker):
        """unique_key in each row must equal the value from the specified column."""
        conn = _make_conn(mocker)
        df = pd.DataFrame({"sku": ["A001", "B002"], "price": [9.99, 19.99]})
        upsert_to_clean_records(df, self.DATASET_ID, conn, unique_key_column="sku")
        _sql, rows = conn.execute.call_args.args
        assert rows[0]["unique_key"] == "A001"
        assert rows[1]["unique_key"] == "B002"

    def test_defaults_to_first_column_as_unique_key(self, mocker):
        """When unique_key_column is None, first column is used."""
        conn = _make_conn(mocker)
        df = pd.DataFrame({"order_id": [100, 200], "amount": [50, 75]})
        upsert_to_clean_records(df, self.DATASET_ID, conn)
        _sql, rows = conn.execute.call_args.args
        assert rows[0]["unique_key"] == "100"
        assert rows[1]["unique_key"] == "200"

    def test_dataset_id_set_on_every_row(self, mocker):
        """Every row must carry the correct dataset_id."""
        conn = _make_conn(mocker)
        df = pd.DataFrame({"id": [1, 2], "v": ["x", "y"]})
        upsert_to_clean_records(df, self.DATASET_ID, conn, unique_key_column="id")
        _sql, rows = conn.execute.call_args.args
        for row in rows:
            assert row["dataset_id"] == self.DATASET_ID

    def test_fields_is_valid_json_string(self, mocker):
        """Each row''s fields must be a valid JSON string."""
        conn = _make_conn(mocker)
        df = pd.DataFrame({"id": [1], "name": ["alpha"], "score": [3.14]})
        upsert_to_clean_records(df, self.DATASET_ID, conn, unique_key_column="id")
        _sql, rows = conn.execute.call_args.args
        parsed = json.loads(rows[0]["fields"])
        assert parsed["name"] == "alpha"
        assert pytest.approx(parsed["score"], 0.01) == 3.14

    def test_returns_upserted_count(self, mocker):
        """Return dict must contain ''upserted'' key with the number of rows."""
        conn = _make_conn(mocker)
        df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
        result = upsert_to_clean_records(df, self.DATASET_ID, conn, unique_key_column="id")
        assert result["upserted"] == 3

    def test_empty_dataframe_calls_execute_with_empty_rows(self, mocker):
        """An empty DataFrame still calls execute (no-op upsert)."""
        conn = _make_conn(mocker)
        df = pd.DataFrame({"id": pd.Series([], dtype=int), "val": pd.Series([], dtype=str)})
        upsert_to_clean_records(df, self.DATASET_ID, conn, unique_key_column="id")
        conn.execute.assert_called_once()
        _sql, rows = conn.execute.call_args.args
        assert rows == []
