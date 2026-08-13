"""
Base class and shared error for all EaaS connectors.
"""
from abc import ABC, abstractmethod
import pandas as pd


class ConnectorError(Exception):
    """Raised for any recoverable connector failure."""


class BaseConnector(ABC):
    """Abstract base for API / DB connectors."""

    @abstractmethod
    def test_connection(self) -> bool:
        """Return True if the connection succeeds, False otherwise (never raise)."""

    @abstractmethod
    def fetch(self, **kwargs) -> pd.DataFrame:
        """Fetch data and return a DataFrame. Raise ConnectorError on failure."""
