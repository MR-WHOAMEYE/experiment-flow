"""
Tests for FirecrawlConnector (ingestion/connectors/firecrawl_connector.py)

Runs fully offline — all HTTP calls are intercepted by `responses` and `unittest.mock`.
"""

import pytest
import responses as responses_lib
import requests

from ingestion.connectors.firecrawl_connector import FirecrawlConnector
from ingestion.connectors.base import ConnectorError

FAKE_KEY = "fc-testkey123"
BASE = "https://api.firecrawl.dev"


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

class TestFirecrawlConnectorInit:
    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)
        with pytest.raises(ConnectorError, match="no API key"):
            FirecrawlConnector(api_key="")

    def test_picks_up_env_key(self, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "env-key")
        conn = FirecrawlConnector()
        assert conn.api_key == "env-key"

    def test_explicit_key_wins(self, monkeypatch):
        monkeypatch.setenv("FIRECRAWL_API_KEY", "env-key")
        conn = FirecrawlConnector(api_key="explicit-key")
        assert conn.api_key == "explicit-key"

    def test_custom_base_url(self):
        conn = FirecrawlConnector(api_key=FAKE_KEY, base_url="http://localhost:3002")
        assert conn.base_url == "http://localhost:3002"

    def test_trailing_slash_stripped_from_base_url(self):
        conn = FirecrawlConnector(api_key=FAKE_KEY, base_url="http://localhost:3002/")
        assert conn.base_url == "http://localhost:3002"


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------

class TestFirecrawlTestConnection:
    def _make(self):
        return FirecrawlConnector(api_key=FAKE_KEY)

    @responses_lib.activate
    def test_returns_true_on_200(self):
        responses_lib.add(responses_lib.GET, f"{BASE}/", status=200, json={})
        assert self._make().test_connection() is True

    @responses_lib.activate
    def test_returns_false_on_http_error(self):
        responses_lib.add(responses_lib.GET, f"{BASE}/", status=401)
        assert self._make().test_connection() is False

    def test_returns_false_on_connection_error(self, monkeypatch):
        def bad_get(*a, **kw):
            raise requests.ConnectionError("unreachable")
        monkeypatch.setattr(requests, "get", bad_get)
        assert self._make().test_connection() is False


# ---------------------------------------------------------------------------
# fetch — single scrape
# ---------------------------------------------------------------------------

SCRAPE_RESPONSE = {
    "success": True,
    "data": {
        "markdown": "# Hello World\n\nThis is the page content.",
        "metadata": {"title": "Hello World", "sourceURL": "https://example.com"},
    },
}


class TestFirecrawlFetchSingle:
    def _make(self):
        return FirecrawlConnector(api_key=FAKE_KEY)

    @responses_lib.activate
    def test_returns_dataframe_with_expected_columns(self):
        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/scrape",
            json=SCRAPE_RESPONSE,
            status=200,
        )
        df = self._make().fetch(url="https://example.com")
        assert list(df.columns) == ["url", "title", "content", "scraped_at"]

    @responses_lib.activate
    def test_single_row_returned(self):
        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/scrape",
            json=SCRAPE_RESPONSE,
            status=200,
        )
        df = self._make().fetch(url="https://example.com")
        assert len(df) == 1

    @responses_lib.activate
    def test_content_and_title_populated(self):
        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/scrape",
            json=SCRAPE_RESPONSE,
            status=200,
        )
        df = self._make().fetch(url="https://example.com")
        assert df.iloc[0]["title"] == "Hello World"
        assert "Hello World" in df.iloc[0]["content"]

    @responses_lib.activate
    def test_raises_connector_error_on_http_error(self):
        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/scrape",
            json={"error": "unauthorized"},
            status=401,
        )
        with pytest.raises(ConnectorError, match="scrape failed"):
            self._make().fetch(url="https://example.com")

    @responses_lib.activate
    def test_raises_connector_error_when_success_false(self):
        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/scrape",
            json={"success": False, "error": "blocked"},
            status=200,
        )
        with pytest.raises(ConnectorError, match="success=false"):
            self._make().fetch(url="https://example.com")


# ---------------------------------------------------------------------------
# fetch — crawl mode
# ---------------------------------------------------------------------------

CRAWL_SUBMIT_RESPONSE = {"id": "job-abc-123", "success": True}

CRAWL_STATUS_COMPLETED = {
    "status": "completed",
    "data": [
        {
            "markdown": "# Page 1",
            "metadata": {"title": "Page 1", "sourceURL": "https://example.com/page1"},
        },
        {
            "markdown": "# Page 2",
            "metadata": {"title": "Page 2", "sourceURL": "https://example.com/page2"},
        },
    ],
}


class TestFirecrawlFetchCrawl:
    def _make(self):
        return FirecrawlConnector(api_key=FAKE_KEY)

    @responses_lib.activate
    def test_crawl_returns_multiple_rows(self, monkeypatch):
        # Skip the sleep in polling
        monkeypatch.setattr("time.sleep", lambda _: None)

        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/crawl",
            json=CRAWL_SUBMIT_RESPONSE,
            status=200,
        )
        responses_lib.add(
            responses_lib.GET,
            f"{BASE}/v1/crawl/job-abc-123",
            json=CRAWL_STATUS_COMPLETED,
            status=200,
        )
        df = self._make().fetch(url="https://example.com", crawl=True, limit=5)
        assert len(df) == 2
        assert set(df.columns) == {"url", "title", "content", "scraped_at"}

    @responses_lib.activate
    def test_crawl_raises_on_submit_failure(self):
        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/crawl",
            json={"error": "rate limited"},
            status=429,
        )
        with pytest.raises(ConnectorError, match="crawl submission failed"):
            self._make().fetch(url="https://example.com", crawl=True)

    @responses_lib.activate
    def test_crawl_raises_on_failed_status(self, monkeypatch):
        monkeypatch.setattr("time.sleep", lambda _: None)

        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/crawl",
            json=CRAWL_SUBMIT_RESPONSE,
            status=200,
        )
        responses_lib.add(
            responses_lib.GET,
            f"{BASE}/v1/crawl/job-abc-123",
            json={"status": "failed"},
            status=200,
        )
        with pytest.raises(ConnectorError, match="status=failed"):
            self._make().fetch(url="https://example.com", crawl=True)

    @responses_lib.activate
    def test_crawl_raises_when_no_job_id(self):
        responses_lib.add(
            responses_lib.POST,
            f"{BASE}/v1/crawl",
            json={"success": True},  # missing "id"
            status=200,
        )
        with pytest.raises(ConnectorError, match="did not return an id"):
            self._make().fetch(url="https://example.com", crawl=True)
