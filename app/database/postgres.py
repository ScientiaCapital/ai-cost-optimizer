"""PostgreSQL database connection utilities."""
import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager


def get_database_url():
    """Get PostgreSQL database URL from environment.

    Falls back to SQLite for backward compatibility and testing.
    """
    return os.getenv(
        'DATABASE_URL',
        'sqlite:///./optimizer.db'  # Fallback to SQLite
    )


@contextmanager
def get_connection():
    """Get database connection as context manager.

    Supports both PostgreSQL and SQLite based on DATABASE_URL.

    Usage:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    db_url = get_database_url()

    # Check if using SQLite
    if db_url.startswith('sqlite:///'):
        # Extract path from SQLite URL
        db_path = db_url.replace('sqlite:///', './')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
    else:
        # Use PostgreSQL
        conn = psycopg2.connect(db_url)

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

    Supports both PostgreSQL and SQLite cursors.

    Args:
        conn: Database connection
        dict_cursor: If True, return dict-like cursor (rows as dicts)

    Returns:
        Database cursor
    """
    # Check if SQLite connection (has row_factory attribute)
    if hasattr(conn, 'row_factory'):
        # SQLite connection - row_factory already set in get_connection
        return conn.cursor()
    else:
        # PostgreSQL connection
        if dict_cursor:
            return conn.cursor(cursor_factory=RealDictCursor)
        return conn.cursor()
