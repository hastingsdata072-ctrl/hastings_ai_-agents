"""
Database connection management for Hastings RAG Studio.

Uses psycopg v3 (not psycopg2). Provides a context-manager-based
get_connection() function and a connection pool via get_pool().
Registers pgvector types so vector columns are handled automatically.
"""

from contextlib import contextmanager
from typing import Generator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from src.config import config

# Module-level pool (created lazily on first use)
_pool: ConnectionPool | None = None


def _get_pool() -> ConnectionPool:
    """Return the module-level connection pool, creating it if necessary."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=config.database_url,
            min_size=1,
            max_size=10,
            kwargs={"row_factory": dict_row},
            open=True,
        )
    return _pool


@contextmanager
def get_connection(register_vector_type: bool = True) -> Generator[psycopg.Connection, None, None]:
    """
    Context manager that yields a psycopg v3 connection.

    Args:
        register_vector_type: Set to False when calling before the pgvector
                              extension has been created (e.g. during init_db).

    Usage:
        with get_connection() as conn:
            conn.execute("SELECT 1")
    """
    conn = psycopg.connect(config.database_url, row_factory=dict_row)
    try:
        if register_vector_type:
            # Only register after the extension exists in this database
            from pgvector.psycopg import register_vector
            register_vector(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_pool_connection() -> Generator[psycopg.Connection, None, None]:
    """
    Context manager that borrows a connection from the shared pool.

    Prefer this in request-handling code; use get_connection() for
    one-off scripts and initialisation.
    """
    pool = _get_pool()
    with pool.connection() as conn:
        from pgvector.psycopg import register_vector
        register_vector(conn)
        yield conn
