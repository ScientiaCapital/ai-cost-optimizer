"""Tests for PostgreSQL migration to feedback tables."""
import pytest
import psycopg2
from alembic import command
from alembic.config import Config


@pytest.fixture
def alembic_config():
    """Create Alembic config for testing."""
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", "postgresql://test:test@localhost:5432/test_optimizer")
    return config


def test_feedback_tables_migration(alembic_config):
    """Test migration creates response_feedback table."""
    # Run migration
    command.upgrade(alembic_config, "head")

    # Connect and verify table exists
    conn = psycopg2.connect("postgresql://test:test@localhost:5432/test_optimizer")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'response_feedback'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()
    column_names = [col[0] for col in columns]

    assert 'id' in column_names
    assert 'request_id' in column_names
    assert 'quality_score' in column_names
    assert 'is_correct' in column_names
    assert 'prompt_pattern' in column_names

    cursor.close()
    conn.close()


def test_model_performance_history_migration(alembic_config):
    """Test migration creates model_performance_history table."""
    command.upgrade(alembic_config, "head")

    conn = psycopg2.connect("postgresql://test:test@localhost:5432/test_optimizer")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'model_performance_history'
    """)

    columns = [row[0] for row in cursor.fetchall()]

    assert 'pattern' in columns
    assert 'provider' in columns
    assert 'model' in columns
    assert 'avg_quality_score' in columns
    assert 'correctness_rate' in columns
    assert 'sample_count' in columns
    assert 'confidence_level' in columns

    cursor.close()
    conn.close()
