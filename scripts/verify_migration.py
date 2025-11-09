"""Verify SQLite to PostgreSQL migration."""
import sqlite3
import psycopg2
from psycopg2 import sql
import os
import re


def validate_identifier(name):
    """Validate SQL identifier to prevent injection.

    Args:
        name: Identifier to validate

    Raises:
        ValueError: If identifier is invalid
    """
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name}")


def verify_table_counts(sqlite_conn, pg_conn, table_name):
    """Verify row counts match.

    Args:
        sqlite_conn: SQLite connection
        pg_conn: PostgreSQL connection
        table_name: Table to verify

    Returns:
        True if counts match
    """
    # Validate table name to prevent SQL injection
    validate_identifier(table_name)

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # SQLite count (safe - table_name validated)
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    sqlite_count = sqlite_cursor.fetchone()[0]

    # PostgreSQL count (using sql.Identifier for extra safety)
    pg_cursor.execute(
        sql.SQL("SELECT COUNT(*) FROM {table}").format(
            table=sql.Identifier(table_name)
        )
    )
    pg_count = pg_cursor.fetchone()[0]

    match = sqlite_count == pg_count
    status = "✓" if match else "✗"

    print(f"  {status} {table_name}: SQLite={sqlite_count}, PostgreSQL={pg_count}")

    return match


def main():
    """Run verification."""
    print("Verifying migration...\n")

    sqlite_conn = sqlite3.connect('optimizer.db')

    # Secure parameter-based connection
    pg_conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'optimizer'),
        user=os.getenv('DB_USER', 'optimizer_user'),
        password=os.getenv('DB_PASSWORD', 'password')
    )

    # FIX: Add response_feedback to verification
    tables = ['requests', 'routing_metrics', 'response_cache', 'response_feedback']

    all_match = True
    for table in tables:
        try:
            if not verify_table_counts(sqlite_conn, pg_conn, table):
                all_match = False
        except Exception as e:
            print(f"  ✗ {table}: ERROR - {e}")
            all_match = False

    print()
    if all_match:
        print("✓ All table counts match!")
    else:
        print("✗ Some tables have mismatched counts")
        return 1

    sqlite_conn.close()
    pg_conn.close()

    return 0


if __name__ == '__main__':
    exit(main())
