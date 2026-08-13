"""
PostgreSQL Connector -- US-1.2

Uses SQLAlchemy Core (no ORM) so EXPLAIN ANALYZE stays meaningful (per prompt ADR-003).
"""
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from ingestion.connectors.base import BaseConnector, ConnectorError
from ingestion.logger import get_logger

log = get_logger(__name__)


class PostgresConnector(BaseConnector):
    """
    Pull data from a PostgreSQL database via a user-supplied SELECT query.

    Args:
        dsn: Full SQLAlchemy DSN e.g. postgresql+psycopg2://user:pass@host:port/db
    """

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._engine = create_engine(dsn, pool_pre_ping=True)

    def test_connection(self) -> bool:
        """
        Attempt to open a connection.
        Returns True on success, False on any error.
        """
        log.info("postgres_connector.test_connection", extra={"dsn": self.dsn.split("@")[-1]})
        try:
            with self._engine.connect():
                pass
            return True
        except Exception as exc:
            log.warning("postgres_connector.test_connection failed", extra={"error": str(exc)})
            return False

    def fetch(self, query: str, **kwargs) -> pd.DataFrame:
        """
        Execute a SELECT query and return results as a DataFrame.

        Args:
            query: A plain SQL SELECT statement (no parameters for now).

        Raises:
            ConnectorError: If the query fails.
        """
        log.info("postgres_connector.fetch started", extra={"query_preview": query[:80]})
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                columns = list(result.keys())
            df = pd.DataFrame(rows, columns=columns)
        except SQLAlchemyError as exc:
            raise ConnectorError(f"postgres_connector fetch failed: {exc}") from exc
        except Exception as exc:
            raise ConnectorError(f"postgres_connector fetch unexpected error: {exc}") from exc

        log.info("postgres_connector.fetch complete", extra={"rows": len(df)})
        return df
