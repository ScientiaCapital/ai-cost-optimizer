"""Verify SQLite to PostgreSQL migration."""
import sqlite3
import psycopg2
import os


def verify_table_counts(sqlite_conn, pg_conn, table_name):
    """Verify row counts match.

    Args:
        sqlite_conn: SQLite connection
        pg_conn: PostgreSQL connection
        table_name: Table to verify

    Returns:
        True if counts match
    """
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # SQLite count
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    sqlite_count = sqlite_cursor.fetchone()[0]

    # PostgreSQL count
    pg_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    pg_count = pg_cursor.fetchone()[0]

    match = sqlite_count == pg_count
    status = "✓" if match else "✗"

    print(f"  {status} {table_name}: SQLite={sqlite_count}, PostgreSQL={pg_count}")

    return match


def main():
    """Run verification."""
    print("Verifying migration...\n")

    sqlite_conn = sqlite3.connect('optimizer.db')

    db_password = os.getenv('DB_PASSWORD', 'password')
    pg_conn = psycopg2.connect(
        f"postgresql://optimizer_user:{db_password}@localhost:5432/optimizer"
    )

    tables = ['requests', 'routing_metrics', 'response_cache']

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
