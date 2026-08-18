"""
Firecrawl Connector -- Web Scraping via Firecrawl API

Scrapes one or more URLs using the Firecrawl API and returns a DataFrame
with columns: url, title, content (markdown), scraped_at.

Implements BaseConnector so scraped pages flow directly into the existing
raw_ingest / upsert_to_clean_records pipeline.

Usage:
    from ingestion.connectors.firecrawl_connector import FirecrawlConnector
    from ingestion.file_ingestor import upsert_to_clean_records

    conn = FirecrawlConnector(api_key=os.getenv("FIRECRAWL_API_KEY"))
    df = conn.fetch(url="https://example.com")
    # or scrape a whole site:
    df = conn.fetch(url="https://example.com", crawl=True, limit=20)

Environment:
    FIRECRAWL_API_KEY   Your Firecrawl API key (https://firecrawl.dev)
    FIRECRAWL_BASE_URL  Override for self-hosted instance (default: https://api.firecrawl.dev)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import requests

from ingestion.connectors.base import BaseConnector, ConnectorError
from ingestion.logger import get_logger

log = get_logger(__name__)

_DEFAULT_BASE_URL = "https://api.firecrawl.dev"


class FirecrawlConnector(BaseConnector):
    """
    Scrape web pages via the Firecrawl API.

    Args:
        api_key:   Firecrawl API key. Falls back to FIRECRAWL_API_KEY env var.
        base_url:  Firecrawl base URL. Falls back to FIRECRAWL_BASE_URL or the
                   public API at https://api.firecrawl.dev.
        timeout:   Request timeout in seconds (default: 60).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ) -> None:
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "")
        self.base_url = (
            base_url
            or os.getenv("FIRECRAWL_BASE_URL", _DEFAULT_BASE_URL)
        ).rstrip("/")
        self.timeout = timeout

        if not self.api_key:
            raise ConnectorError(
                "FirecrawlConnector: no API key provided. "
                "Set FIRECRAWL_API_KEY in .env or pass api_key= explicitly."
            )

        self._headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # BaseConnector interface
    # ------------------------------------------------------------------

    def test_connection(self) -> bool:
        """
        Ping the Firecrawl health endpoint.
        Returns True on 2xx, False on any error (never raises).
        """
        log.info("firecrawl_connector.test_connection", extra={"base_url": self.base_url})
        try:
            resp = requests.get(
                f"{self.base_url}/",
                headers=self.headers_without_content_type(),
                timeout=10,
            )
            resp.raise_for_status()
            return True
        except Exception as exc:
            log.warning(
                "firecrawl_connector.test_connection failed",
                extra={"error": str(exc)},
            )
            return False

    def fetch(self, url: str, *, crawl: bool = False, limit: int = 10, **kwargs) -> pd.DataFrame:
        """
        Scrape a single page or crawl an entire site.

        Args:
            url:    Target URL to scrape or crawl.
            crawl:  If True, crawl the full site (up to `limit` pages).
                    If False (default), scrape a single page.
            limit:  Max pages when crawl=True (default 10).
            **kwargs: Additional payload fields forwarded to Firecrawl API.

        Returns:
            DataFrame with columns: url, title, content, scraped_at

        Raises:
            ConnectorError: On network error or non-2xx response.
        """
        if crawl:
            return self._crawl(url, limit=limit, **kwargs)
        return self._scrape_one(url, **kwargs)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scrape_one(self, url: str, **kwargs) -> pd.DataFrame:
        """Call /v1/scrape for a single URL."""
        log.info("firecrawl_connector.scrape", extra={"url": url})
        endpoint = f"{self.base_url}/v1/scrape"
        payload = {"url": url, "formats": ["markdown"], **kwargs}

        try:
            resp = requests.post(
                endpoint,
                headers=self._headers,
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise ConnectorError(
                f"firecrawl_connector: scrape failed for {url} "
                f"[HTTP {exc.response.status_code}]: {exc.response.text}"
            ) from exc
        except Exception as exc:
            raise ConnectorError(
                f"firecrawl_connector: request error for {url}: {exc}"
            ) from exc

        body = resp.json()
        if not body.get("success"):
            raise ConnectorError(
                f"firecrawl_connector: API returned success=false for {url}. "
                f"Response: {body}"
            )

        data = body.get("data", {})
        row = {
            "url": url,
            "title": data.get("metadata", {}).get("title", ""),
            "content": data.get("markdown", ""),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        }
        df = pd.DataFrame([row])
        log.info("firecrawl_connector.scrape complete", extra={"url": url, "rows": len(df)})
        return df

    def _crawl(self, url: str, limit: int = 10, **kwargs) -> pd.DataFrame:
        """
        Call /v1/crawl to spider an entire site (async polling pattern).
        Polls /v1/crawl/{job_id} until the job completes or fails.
        """
        log.info("firecrawl_connector.crawl started", extra={"url": url, "limit": limit})
        endpoint = f"{self.base_url}/v1/crawl"
        payload = {"url": url, "limit": limit, "scrapeOptions": {"formats": ["markdown"]}, **kwargs}

        # Step 1: submit the crawl job
        try:
            resp = requests.post(
                endpoint,
                headers=self._headers,
                json=payload,
                timeout=self.timeout,
            )
            resp.raise_for_status()
        except requests.HTTPError as exc:
            raise ConnectorError(
                f"firecrawl_connector: crawl submission failed for {url} "
                f"[HTTP {exc.response.status_code}]: {exc.response.text}"
            ) from exc
        except Exception as exc:
            raise ConnectorError(
                f"firecrawl_connector: crawl request error for {url}: {exc}"
            ) from exc

        body = resp.json()
        job_id = body.get("id")
        if not job_id:
            raise ConnectorError(
                f"firecrawl_connector: crawl job did not return an id. Response: {body}"
            )

        # Step 2: poll for completion
        status_url = f"{self.base_url}/v1/crawl/{job_id}"
        import time

        max_polls = 60  # poll up to 60 times (60s total at 1s intervals)
        for attempt in range(max_polls):
            time.sleep(1)
            try:
                status_resp = requests.get(
                    status_url, headers=self.headers_without_content_type(), timeout=30
                )
                status_resp.raise_for_status()
            except Exception as exc:
                raise ConnectorError(
                    f"firecrawl_connector: poll error for job {job_id}: {exc}"
                ) from exc

            status_body = status_resp.json()
            job_status = status_body.get("status", "")

            if job_status == "completed":
                log.info(
                    "firecrawl_connector.crawl completed",
                    extra={"job_id": job_id, "attempts": attempt + 1},
                )
                return self._parse_crawl_results(status_body)
            if job_status in ("failed", "cancelled"):
                raise ConnectorError(
                    f"firecrawl_connector: crawl job {job_id} ended with status={job_status}."
                )

        raise ConnectorError(
            f"firecrawl_connector: crawl job {job_id} did not complete after {max_polls}s."
        )

    def _parse_crawl_results(self, status_body: dict) -> pd.DataFrame:
        """Parse the completed crawl result into a DataFrame."""
        rows = []
        scraped_at = datetime.now(timezone.utc).isoformat()
        for page in status_body.get("data", []):
            rows.append(
                {
                    "url": page.get("metadata", {}).get("sourceURL", ""),
                    "title": page.get("metadata", {}).get("title", ""),
                    "content": page.get("markdown", ""),
                    "scraped_at": scraped_at,
                }
            )
        df = pd.DataFrame(rows)
        log.info(
            "firecrawl_connector.parse_crawl_results",
            extra={"pages_found": len(df)},
        )
        return df

    def headers_without_content_type(self) -> dict:
        """Return auth headers without Content-Type (for GET requests)."""
        return {"Authorization": f"Bearer {self.api_key}"}
