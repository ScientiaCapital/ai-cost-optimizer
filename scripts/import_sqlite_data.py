"""Import SQLite data to PostgreSQL."""
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os


def get_postgres_conn():
    """Get PostgreSQL connection."""
    db_password = os.getenv('DB_PASSWORD', 'password')
    return psycopg2.connect(
        f"postgresql://optimizer_user:{db_password}@localhost:5432/optimizer"
    )


def migrate_table(sqlite_conn, pg_conn, table_name, column_mapping=None):
    """Migrate a table from SQLite to PostgreSQL.

    Args:
        sqlite_conn: SQLite connection
        pg_conn: PostgreSQL connection
        table_name: Table to migrate
        column_mapping: Optional dict to rename columns
    """
    print(f"  Migrating {table_name}...")

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all rows
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()

    if not rows:
        print(f"    No data in {table_name}")
        return

    # Get column names
    columns = [desc[0] for desc in sqlite_cursor.description]

    # Apply column mapping if provided
    if column_mapping:
        columns = [column_mapping.get(col, col) for col in columns]

    # Insert into PostgreSQL
    insert_sql = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES %s
        ON CONFLICT DO NOTHING
    """

    execute_values(pg_cursor, insert_sql, rows)
    pg_conn.commit()

    print(f"    ✓ Migrated {len(rows)} rows")


def main():
    """Run migration."""
    print("Connecting to databases...")

    sqlite_conn = sqlite3.connect('optimizer.db')
    pg_conn = get_postgres_conn()

    print("Starting data migration...\n")

    # Migrate tables in dependency order
    tables = [
        'requests',
        'routing_metrics',
        'response_cache',
        'response_feedback'
    ]

    for table in tables:
        try:
            migrate_table(sqlite_conn, pg_conn, table)
        except Exception as e:
            print(f"    ERROR: {e}")
            # Continue with other tables

    print("\nData migration complete!")

    sqlite_conn.close()
    pg_conn.close()


if __name__ == '__main__':
    main()
