"""Database connection helpers and Postgres-backed catalog repository."""

from .pool import close_pool, get_connection, get_pool, _psql_available

if _psql_available:
    from .pg_repository import PgCatalogRepository
else:
    PgCatalogRepository = None

__all__ = ["PgCatalogRepository", "close_pool", "get_connection", "get_pool"]
