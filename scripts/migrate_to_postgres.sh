#!/bin/bash
set -e

echo "========================================="
echo "SQLite to PostgreSQL Migration"
echo "========================================="

# Check if SQLite database exists
if [ ! -f "optimizer.db" ]; then
    echo "ERROR: optimizer.db not found"
    exit 1
fi

# Backup SQLite database
echo "1. Backing up SQLite database..."
cp optimizer.db optimizer.db.backup
echo "   ✓ Backup created: optimizer.db.backup"

# Export SQLite data
echo "2. Exporting SQLite data..."
sqlite3 optimizer.db .dump > sqlite_export.sql
echo "   ✓ Data exported to sqlite_export.sql"

# Start PostgreSQL
echo "3. Starting PostgreSQL..."
docker-compose up -d postgres
echo "   ✓ PostgreSQL container started"

# Wait for PostgreSQL to be ready
echo "4. Waiting for PostgreSQL..."
sleep 10

MAX_RETRIES=30
for i in $(seq 1 $MAX_RETRIES); do
    if docker exec optimizer-db pg_isready -U optimizer_user > /dev/null 2>&1; then
        echo "   ✓ PostgreSQL is ready"
        break
    fi

    if [ $i -eq $MAX_RETRIES ]; then
        echo "   ERROR: PostgreSQL failed to start"
        exit 1
    fi

    echo "   Waiting... ($i/$MAX_RETRIES)"
    sleep 2
done

# Run Alembic migrations
echo "5. Running Alembic migrations..."
alembic upgrade head
echo "   ✓ Database schema created"

# Import SQLite data
echo "6. Importing SQLite data to PostgreSQL..."
python scripts/import_sqlite_data.py
echo "   ✓ Data imported successfully"

# Verify migration
echo "7. Verifying migration..."
python scripts/verify_migration.py
echo "   ✓ Migration verified"

echo "========================================="
echo "Migration complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update .env with DATABASE_URL for PostgreSQL"
echo "2. Start all services: docker-compose up -d"
echo "3. Test API: curl http://localhost:8000/health"
