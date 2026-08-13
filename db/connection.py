"""
Shared database connection helpers for the EaaS platform.

All pipeline modules import from here — never construct engines directly.

Usage:
    from db.connection import get_engine, get_connection

    engine = get_engine()
    with get_connection() as conn:
        conn.execute(text("SELECT 1"))
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text, Connection
from sqlalchemy.engine import Engine


def get_engine(database_url: str | None = None) -> Engine:
    """
    Return a SQLAlchemy engine.

    Args:
        database_url: Override the DATABASE_URL env var (useful in tests).

    Returns:
        A SQLAlchemy Engine connected to PostgreSQL.

    Raises:
        RuntimeError: If DATABASE_URL is not set and no override is provided.
    """
    url = database_url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Copy .env.example to .env and fill in credentials."
        )
    return create_engine(url, pool_pre_ping=True)


@contextmanager
def get_connection(
    database_url: str | None = None,
) -> Generator[Connection, None, None]:
    """
    Context manager yielding a SQLAlchemy Connection with auto-commit on success
    and auto-rollback on exception.

    Usage:
        with get_connection() as conn:
            conn.execute(text("INSERT INTO ..."))
    """
    engine = get_engine(database_url)
    with engine.begin() as conn:
        yield conn
