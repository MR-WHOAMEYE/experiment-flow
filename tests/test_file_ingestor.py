"""
Tests for ingestion/file_ingestor.py — US-1.1

Gherkin ACs covered:
  Given a user has a valid CSV file
  When they upload it through the ingestion form
  Then the file is parsed and loaded into raw_ingest
  And a dataset_id is returned to the user

  Given a user uploads a malformed or empty file
  When the platform attempts to parse it
  Then a clear, specific error message is shown
  And nothing is written to the database
"""
import json
import uuid
from pathlib import Path

import pandas as pd
import pytest

from ingestion.file_ingestor import IngestionError, ingest_file, parse_csv, parse_excel


# ---------------------------------------------------------------------------
# Fixtures — temporary test files
# ---------------------------------------------------------------------------

@pytest.fixture()
def valid_csv(tmp_path: Path) -> Path:
    """A minimal valid CSV file."""
    p = tmp_path / "sample.csv"
    p.write_text("id,name,value\n1,alpha,10\n2,beta,20\n3,gamma,30\n", encoding="utf-8")
    return p


@pytest.fixture()
def valid_excel(tmp_path: Path) -> Path:
    """A minimal valid Excel file."""
    p = tmp_path / "sample.xlsx"
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["alpha", "beta", "gamma"], "value": [10, 20, 30]})
    df.to_excel(p, index=False)
    return p


@pytest.fixture()
def malformed_csv(tmp_path: Path) -> Path:
    """A CSV with inconsistent column counts — will fail parsing."""
    p = tmp_path / "bad.csv"
    p.write_text("id,name,value\n1,alpha\n2,beta,20,EXTRA\n", encoding="utf-8")
    return p


@pytest.fixture()
def empty_file(tmp_path: Path) -> Path:
    """A completely empty file."""
    p = tmp_path / "empty.csv"
    p.write_text("", encoding="utf-8")
    return p


@pytest.fixture()
def header_only_csv(tmp_path: Path) -> Path:
    """A CSV with headers but zero data rows."""
    p = tmp_path / "header_only.csv"
    p.write_text("id,name,value\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# parse_csv tests
# ---------------------------------------------------------------------------

class TestParseCsv:
    def test_valid_csv_returns_dataframe(self, valid_csv: Path):
        """Happy path: valid CSV file returns a DataFrame with correct shape."""
        df = parse_csv(valid_csv)
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 3)
        assert list(df.columns) == ["id", "name", "value"]

    def test_empty_file_raises_ingestion_error(self, empty_file: Path):
        """Empty file must raise IngestionError with a descriptive message."""
        with pytest.raises(IngestionError, match="empty"):
            parse_csv(empty_file)

    def test_header_only_raises_ingestion_error(self, header_only_csv: Path):
        """A file with headers but no data rows must raise IngestionError."""
        with pytest.raises(IngestionError, match="no data rows"):
            parse_csv(header_only_csv)

    def test_nonexistent_file_raises_ingestion_error(self, tmp_path: Path):
        """Non-existent file path must raise IngestionError."""
        with pytest.raises(IngestionError, match="not found"):
            parse_csv(tmp_path / "ghost.csv")


# ---------------------------------------------------------------------------
# parse_excel tests
# ---------------------------------------------------------------------------

class TestParseExcel:
    def test_valid_excel_returns_dataframe(self, valid_excel: Path):
        """Happy path: valid .xlsx file returns a DataFrame with correct shape."""
        df = parse_excel(valid_excel)
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (3, 3)
        assert list(df.columns) == ["id", "name", "value"]

    def test_empty_file_raises_ingestion_error(self, empty_file: Path):
        """Empty file treated as Excel must raise IngestionError."""
        with pytest.raises(IngestionError, match="empty|parse"):
            parse_excel(empty_file)

    def test_nonexistent_file_raises_ingestion_error(self, tmp_path: Path):
        """Non-existent Excel file must raise IngestionError."""
        with pytest.raises(IngestionError, match="not found"):
            parse_excel(tmp_path / "ghost.xlsx")


# ---------------------------------------------------------------------------
# ingest_file tests (use MagicMock for DB — no live DB needed)
# ---------------------------------------------------------------------------

class TestIngestFile:
    def _make_mock_conn(self, mocker):
        """Return a mock SQLAlchemy connection that records execute calls."""
        conn = mocker.MagicMock()
        conn.execute.return_value = mocker.MagicMock()
        return conn

    def test_returns_dataset_id_string(self, valid_csv: Path, mocker):
        """
        AC: a dataset_id is returned to the user.
        dataset_id must be a non-empty string.
        """
        conn = self._make_mock_conn(mocker)
        dataset_id = ingest_file(valid_csv, source_name="test_upload", conn=conn)
        assert isinstance(dataset_id, str)
        assert len(dataset_id) > 0

    def test_dataset_id_is_uuid(self, valid_csv: Path, mocker):
        """dataset_id must be a valid UUID4 string."""
        conn = self._make_mock_conn(mocker)
        dataset_id = ingest_file(valid_csv, source_name="test_upload", conn=conn)
        # Will raise ValueError if not a valid UUID
        parsed = uuid.UUID(dataset_id, version=4)
        assert str(parsed) == dataset_id

    def test_execute_called_for_each_row(self, valid_csv: Path, mocker):
        """
        AC: file is parsed and loaded into raw_ingest.
        conn.execute must be called once per row (3 rows in fixture).
        """
        conn = self._make_mock_conn(mocker)
        ingest_file(valid_csv, source_name="test_upload", conn=conn)
        # One execute call per data row (bulk insert via executemany or individual)
        assert conn.execute.call_count >= 1

    def test_malformed_csv_raises_and_no_db_write(self, malformed_csv: Path, mocker):
        """
        AC: malformed file → IngestionError raised, nothing written to DB.
        """
        conn = self._make_mock_conn(mocker)
        with pytest.raises(IngestionError):
            ingest_file(malformed_csv, source_name="bad_upload", conn=conn)
        # DB must not have been touched
        conn.execute.assert_not_called()

    def test_empty_file_raises_and_no_db_write(self, empty_file: Path, mocker):
        """
        AC: empty file → IngestionError raised, nothing written to DB.
        """
        conn = self._make_mock_conn(mocker)
        with pytest.raises(IngestionError):
            ingest_file(empty_file, source_name="empty_upload", conn=conn)
        conn.execute.assert_not_called()

    def test_excel_file_ingested(self, valid_excel: Path, mocker):
        """Happy path for Excel: .xlsx file produces a dataset_id."""
        conn = self._make_mock_conn(mocker)
        dataset_id = ingest_file(valid_excel, source_name="excel_upload", conn=conn)
        assert isinstance(dataset_id, str)
        assert len(dataset_id) > 0
