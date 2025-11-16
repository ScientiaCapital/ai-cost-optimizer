import os
import sqlite3
import pytest
import asyncio
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup test database URL for tests.

    This fixture only sets up SQLite for non-PostgreSQL tests.
    PostgreSQL tests should use TEST_DATABASE_URL environment variable
    and manage their own database state via Alembic migrations.
    """
    # Skip if TEST_DATABASE_URL is set (indicates PostgreSQL tests)
    if os.getenv('TEST_DATABASE_URL'):
        yield
        return

    # Use SQLite for tests (simpler, faster)
    db_path = './test_feedback.db'
    os.environ['DATABASE_URL'] = f'sqlite:///{db_path}'

    # Create test database tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create routing_metrics table (needed for foreign key)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS routing_metrics (
            id INTEGER PRIMARY KEY,
            request_id TEXT UNIQUE NOT NULL,
            selected_provider TEXT,
            selected_model TEXT,
            pattern_detected TEXT,
            complexity_score REAL
        )
    """)

    # Create response_feedback table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS response_feedback (
            id INTEGER PRIMARY KEY,
            request_id TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            quality_score INTEGER NOT NULL,
            is_correct BOOLEAN,
            is_helpful BOOLEAN,
            prompt_pattern TEXT,
            selected_provider TEXT,
            selected_model TEXT,
            complexity_score REAL,
            user_id TEXT,
            session_id TEXT,
            comment TEXT,
            FOREIGN KEY (request_id) REFERENCES routing_metrics(request_id)
        )
    """)

    conn.commit()
    conn.close()

    yield

    # Cleanup
    try:
        os.remove(db_path)
    except:
        pass


@pytest.fixture(scope="function")
def client():
    """Get test client."""
    # TODO: Add database fixture override when testing endpoints that persist data
    # See: docs/plans/2025-10-30-revenue-model-production-ready.md Task 1.1 Step 2
    # For now, router tests don't interact with database so simplified version is fine
    yield TestClient(app)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
