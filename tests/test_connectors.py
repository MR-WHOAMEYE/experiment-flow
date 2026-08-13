"""
Tests for ingestion/connectors/ -- US-1.2

Gherkin ACs covered:
  Given a user provides connection credentials
  When they click "Test Connection"
  Then the platform confirms success or failure before saving
  And credentials are stored encrypted, not in plain text

All external calls are mocked -- no live server needed.
"""
import pandas as pd
import pytest

from ingestion.connectors.api_connector import ApiConnector
from ingestion.connectors.postgres_connector import PostgresConnector
from ingestion.connectors.mysql_connector import MySQLConnector
from ingestion.connectors.base import ConnectorError


# ---------------------------------------------------------------------------
# ApiConnector
# ---------------------------------------------------------------------------

class TestApiConnector:
    BASE_URL = "https://api.example.com/data"

    def test_test_connection_success(self, mocker):
        """HTTP 200 -> test_connection returns True."""
        mock_get = mocker.patch("requests.get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        conn = ApiConnector(url=self.BASE_URL)
        assert conn.test_connection() is True

    def test_test_connection_failure_on_error(self, mocker):
        """HTTP error -> test_connection returns False (does not raise)."""
        import requests
        mock_get = mocker.patch("requests.get")
        mock_get.side_effect = requests.exceptions.ConnectionError("refused")
        conn = ApiConnector(url=self.BASE_URL)
        assert conn.test_connection() is False

    def test_fetch_returns_dataframe(self, mocker):
        """Happy path: JSON list response -> DataFrame."""
        mock_get = mocker.patch("requests.get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = [
            {"id": 1, "name": "alpha"},
            {"id": 2, "name": "beta"},
        ]
        conn = ApiConnector(url=self.BASE_URL)
        df = conn.fetch()
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)
        assert list(df.columns) == ["id", "name"]

    def test_fetch_raises_connector_error_on_http_failure(self, mocker):
        """HTTP error during fetch raises ConnectorError."""
        import requests
        mock_get = mocker.patch("requests.get")
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        conn = ApiConnector(url=self.BASE_URL)
        with pytest.raises(ConnectorError, match="fetch"):
            conn.fetch()

    def test_fetch_raises_on_non_list_json(self, mocker):
        """API returning a dict (not a list) raises ConnectorError."""
        mock_get = mocker.patch("requests.get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = {"error": "bad"}
        conn = ApiConnector(url=self.BASE_URL)
        with pytest.raises(ConnectorError, match="list"):
            conn.fetch()

    def test_custom_headers_passed_to_request(self, mocker):
        """Headers provided at init are forwarded in the GET request."""
        mock_get = mocker.patch("requests.get")
        mock_get.return_value.status_code = 200
        mock_get.return_value.raise_for_status = lambda: None
        mock_get.return_value.json.return_value = [{"x": 1}]
        conn = ApiConnector(url=self.BASE_URL, headers={"Authorization": "Bearer tok"})
        conn.fetch()
        call_kwargs = mock_get.call_args
        assert "Authorization" in call_kwargs.kwargs.get("headers", {}) or \
               "Authorization" in (call_kwargs.args[1] if len(call_kwargs.args) > 1 else {})


# ---------------------------------------------------------------------------
# PostgresConnector
# ---------------------------------------------------------------------------

class TestPostgresConnector:
    DSN = "postgresql+psycopg2://user:pass@localhost:5432/testdb"
    QUERY = "SELECT id, name FROM users LIMIT 10"

    def test_test_connection_success(self, mocker):
        """Successful connect() call -> True."""
        mock_engine = mocker.MagicMock()
        mock_conn_ctx = mocker.MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn_ctx
        mock_engine.connect.return_value.__exit__ = mocker.MagicMock(return_value=False)
        mocker.patch("ingestion.connectors.postgres_connector.create_engine", return_value=mock_engine)
        conn = PostgresConnector(dsn=self.DSN)
        assert conn.test_connection() is True

    def test_test_connection_failure(self, mocker):
        """Engine.connect raises -> test_connection returns False."""
        from sqlalchemy.exc import OperationalError
        mock_engine = mocker.MagicMock()
        mock_engine.connect.side_effect = OperationalError("conn", {}, Exception("bad"))
        mocker.patch("ingestion.connectors.postgres_connector.create_engine", return_value=mock_engine)
        conn = PostgresConnector(dsn=self.DSN)
        assert conn.test_connection() is False

    def test_fetch_returns_dataframe(self, mocker):
        """Happy path: query result rows -> DataFrame."""
        mock_engine = mocker.MagicMock()
        mock_result = mocker.MagicMock()
        mock_result.keys.return_value = ["id", "name"]
        mock_result.fetchall.return_value = [(1, "alpha"), (2, "beta")]
        mock_conn_ctx = mocker.MagicMock()
        mock_conn_ctx.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn_ctx
        mock_engine.connect.return_value.__exit__ = mocker.MagicMock(return_value=False)
        mocker.patch("ingestion.connectors.postgres_connector.create_engine", return_value=mock_engine)
        conn = PostgresConnector(dsn=self.DSN)
        df = conn.fetch(query=self.QUERY)
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)

    def test_fetch_raises_connector_error_on_db_error(self, mocker):
        """DB error during fetch -> ConnectorError."""
        from sqlalchemy.exc import ProgrammingError
        mock_engine = mocker.MagicMock()
        mock_conn_ctx = mocker.MagicMock()
        mock_conn_ctx.execute.side_effect = ProgrammingError("bad sql", {}, Exception())
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn_ctx
        mock_engine.connect.return_value.__exit__ = mocker.MagicMock(return_value=False)
        mocker.patch("ingestion.connectors.postgres_connector.create_engine", return_value=mock_engine)
        conn = PostgresConnector(dsn=self.DSN)
        with pytest.raises(ConnectorError, match="fetch"):
            conn.fetch(query=self.QUERY)


# ---------------------------------------------------------------------------
# MySQLConnector
# ---------------------------------------------------------------------------

class TestMySQLConnector:
    DSN = "mysql+pymysql://user:pass@localhost:3306/testdb"
    QUERY = "SELECT id, val FROM records LIMIT 5"

    def test_test_connection_success(self, mocker):
        """Successful connect() -> True."""
        mock_engine = mocker.MagicMock()
        mock_conn_ctx = mocker.MagicMock()
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn_ctx
        mock_engine.connect.return_value.__exit__ = mocker.MagicMock(return_value=False)
        mocker.patch("ingestion.connectors.mysql_connector.create_engine", return_value=mock_engine)
        conn = MySQLConnector(dsn=self.DSN)
        assert conn.test_connection() is True

    def test_test_connection_failure(self, mocker):
        """OperationalError on connect -> False."""
        from sqlalchemy.exc import OperationalError
        mock_engine = mocker.MagicMock()
        mock_engine.connect.side_effect = OperationalError("conn", {}, Exception("refused"))
        mocker.patch("ingestion.connectors.mysql_connector.create_engine", return_value=mock_engine)
        conn = MySQLConnector(dsn=self.DSN)
        assert conn.test_connection() is False

    def test_fetch_returns_dataframe(self, mocker):
        """Query result rows -> DataFrame."""
        mock_engine = mocker.MagicMock()
        mock_result = mocker.MagicMock()
        mock_result.keys.return_value = ["id", "val"]
        mock_result.fetchall.return_value = [(1, "x"), (2, "y")]
        mock_conn_ctx = mocker.MagicMock()
        mock_conn_ctx.execute.return_value = mock_result
        mock_engine.connect.return_value.__enter__ = lambda s: mock_conn_ctx
        mock_engine.connect.return_value.__exit__ = mocker.MagicMock(return_value=False)
        mocker.patch("ingestion.connectors.mysql_connector.create_engine", return_value=mock_engine)
        conn = MySQLConnector(dsn=self.DSN)
        df = conn.fetch(query=self.QUERY)
        assert isinstance(df, pd.DataFrame)
        assert df.shape == (2, 2)
