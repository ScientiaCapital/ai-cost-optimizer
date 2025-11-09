"""Import SQLite data to PostgreSQL."""
import sqlite3
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
import os
import re


def validate_identifier(name):
    """Validate SQL identifier to prevent injection.

    Args:
        name: Identifier to validate (table or column name)

    Raises:
        ValueError: If identifier contains invalid characters
    """
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"Invalid SQL identifier: {name}")


def get_postgres_conn():
    """Get PostgreSQL connection with secure parameters."""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'optimizer'),
        user=os.getenv('DB_USER', 'optimizer_user'),
        password=os.getenv('DB_PASSWORD', 'password')
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

    # Validate table name to prevent SQL injection
    validate_identifier(table_name)

    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()

    # Get all rows (safe - table_name validated)
    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
    rows = sqlite_cursor.fetchall()

    if not rows:
        print(f"    No data in {table_name}")
        return

    # Get column names
    columns = [desc[0] for desc in sqlite_cursor.description]

    # Validate all column names
    for col in columns:
        validate_identifier(col)

    # Apply column mapping if provided
    if column_mapping:
        columns = [column_mapping.get(col, col) for col in columns]
        # Re-validate mapped columns
        for col in columns:
            validate_identifier(col)

    # Insert into PostgreSQL using sql.Identifier for safety
    insert_sql = sql.SQL("""
        INSERT INTO {table} ({columns})
        VALUES %s
        ON CONFLICT DO NOTHING
    """).format(
        table=sql.Identifier(table_name),
        columns=sql.SQL(', ').join(sql.Identifier(col) for col in columns)
    )

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
