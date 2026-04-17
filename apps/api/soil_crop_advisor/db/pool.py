from __future__ import annotations

import logging
import os
from typing import Iterator

from psycopg_pool import ConnectionPool

_logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None


def get_database_url() -> str | None:
    """Return Postgres connection string when `DATABASE_URL` is set."""
    raw = os.getenv("DATABASE_URL")
    if raw is None or not raw.strip():
        return None
    return raw.strip()


def get_pool() -> ConnectionPool | None:
    """Lazily open a shared connection pool (or None when DB is not configured)."""
    global _pool
    url = get_database_url()
    if url is None:
        return None
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=url,
            min_size=1,
            max_size=10,
            open=True,
            kwargs={"connect_timeout": 10},
        )
        _logger.info("database pool opened")
    return _pool


def close_pool() -> None:
    """Close the pool during application shutdown."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
        _logger.info("database pool closed")


def get_connection() -> Iterator[None]:
    """Context-style helper for tests; prefer `get_pool().connection()` in app code."""
    pool = get_pool()
    if pool is None:
        raise RuntimeError("DATABASE_URL is not set")
    with pool.connection():
        yield None
