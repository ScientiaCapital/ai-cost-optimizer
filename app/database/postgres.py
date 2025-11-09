"""PostgreSQL database connection utilities."""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


def get_database_url():
    """Get PostgreSQL database URL from environment."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError(
            "DATABASE_URL environment variable is required. "
            "Example: postgresql://user:password@localhost:5432/optimizer"
        )
    return db_url


@contextmanager
def get_connection():
    """Get database connection as context manager.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    conn = psycopg2.connect(get_database_url())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_cursor(conn, dict_cursor=True):
    """Get cursor from connection.

    Args:
        conn: Database connection
        dict_cursor: If True, return RealDictCursor (rows as dicts)

    Returns:
        Database cursor
    """
    if dict_cursor:
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()
