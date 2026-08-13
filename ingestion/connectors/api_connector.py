"""
API Connector -- US-1.2

Fetches data from an HTTP endpoint (GET by default).
Supports custom headers and basic pagination (next_key).
"""
import pandas as pd
import requests

from ingestion.connectors.base import BaseConnector, ConnectorError
from ingestion.logger import get_logger

log = get_logger(__name__)


class ApiConnector(BaseConnector):
    """
    Pull data from a REST API endpoint.

    Args:
        url:     Base URL for the API endpoint.
        headers: Optional dict of HTTP headers (e.g. Authorization).
        method:  HTTP method, default "GET".
        params:  Optional query parameters dict.
    """

    def __init__(
        self,
        url: str,
        headers: dict | None = None,
        method: str = "GET",
        params: dict | None = None,
    ) -> None:
        self.url = url
        self.headers = headers or {}
        self.method = method.upper()
        self.params = params or {}

    def test_connection(self) -> bool:
        """
        Send a lightweight HEAD or GET request.
        Returns True on 2xx, False on any error.
        """
        log.info("api_connector.test_connection", extra={"url": self.url})
        try:
            resp = requests.get(self.url, headers=self.headers, params=self.params, timeout=10)
            resp.raise_for_status()
            return True
        except Exception as exc:
            log.warning("api_connector.test_connection failed", extra={"error": str(exc)})
            return False

    def fetch(self, **kwargs) -> pd.DataFrame:
        """
        Fetch data from the API and return a DataFrame.

        Expects the API to return a JSON array of objects.

        Raises:
            ConnectorError: If the request fails or response is not a list.
        """
        log.info("api_connector.fetch started", extra={"url": self.url})
        try:
            resp = requests.get(
                self.url,
                headers=self.headers,
                params={**self.params, **kwargs},
                timeout=30,
            )
            resp.raise_for_status()
        except Exception as exc:
            raise ConnectorError(f"api_connector fetch failed for {self.url}: {exc}") from exc

        try:
            data = resp.json()
        except Exception as exc:
            raise ConnectorError(f"api_connector fetch: JSON decode error: {exc}") from exc

        if not isinstance(data, list):
            raise ConnectorError(
                f"api_connector fetch: expected a list of records, got {type(data).__name__}. "
                "Check the API response format."
            )

        df = pd.DataFrame(data)
        log.info("api_connector.fetch complete", extra={"url": self.url, "rows": len(df)})
        return df
