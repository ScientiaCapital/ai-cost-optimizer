"""
Tests for AsyncConnectionPool

This test suite validates async PostgreSQL connection pooling:
- Pool initialization and lifecycle management
- Connection acquisition and release
- Concurrent connection handling
- Error handling and recovery
- Pool size limits and connection reuse

Test Requirements:
    - PostgreSQL database must be running
    - DATABASE_URL environment variable must be set
    - Format: postgresql://user:password@host:port/database

Running Tests:
    # Using Docker Compose (recommended):
    docker-compose up -d
    export DATABASE_URL="postgresql://optimizer_user:optimizer_pass@localhost:5432/optimizer_db"
    pytest tests/test_async_pool.py -v

    # Or run tests inside Docker container:
    docker run --rm --network ai-cost-optimizer_optimizer-network \
      -e DATABASE_URL="postgresql://optimizer_user:optimizer_pass@optimizer-db:5432/optimizer_db" \
      -v $(pwd):/app -w /app ai-cost-optimizer-api \
      pytest tests/test_async_pool.py -v

Note: All tests are automatically skipped if PostgreSQL is not available.
"""

import pytest
import asyncio
import os
from app.database.async_pool import AsyncConnectionPool


# Skip all tests if no PostgreSQL available
pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL", "").startswith("postgresql"),
    reason="PostgreSQL not available (DATABASE_URL not set)"
)


@pytest.fixture
async def pool():
    """Create and teardown async pool for testing."""
    # Use test database URL
    db_url = os.getenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

    pool = AsyncConnectionPool(database_url=db_url, min_size=2, max_size=5)
    await pool.initialize()

    yield pool

    await pool.close()


class TestPoolInitialization:
    """Test pool initialization and configuration."""

    async def test_pool_initializes_successfully(self, pool):
        """Pool initializes with correct configuration."""
        assert pool.is_initialized is True
        assert pool.min_size == 2
        assert pool.max_size == 5

    async def test_pool_creates_minimum_connections(self, pool):
        """Pool creates minimum number of connections on init."""
        # Pool should have at least min_size connections available
        assert pool.get_size() >= pool.min_size

    async def test_pool_initialization_with_invalid_url(self):
        """Pool initialization fails gracefully with invalid URL."""
        pool = AsyncConnectionPool(
            database_url="postgresql://invalid:invalid@nonexistent:5432/fake",
            min_size=1,
            max_size=2
        )

        with pytest.raises(Exception):  # Should raise connection error
            await pool.initialize()

    async def test_pool_double_initialization_is_idempotent(self, pool):
        """Calling initialize() twice doesn't create duplicate connections."""
        # Initialize again
        await pool.initialize()

        # Should still have correct configuration
        assert pool.is_initialized is True
        assert pool.get_size() <= pool.max_size


class TestConnectionAcquisition:
    """Test connection acquisition from pool."""

    async def test_acquire_connection_from_pool(self, pool):
        """Can acquire a connection from the pool."""
        async with pool.acquire() as conn:
            assert conn is not None

            # Should be able to execute queries
            result = await conn.fetchval("SELECT 1")
            assert result == 1

    async def test_connection_returns_to_pool(self, pool):
        """Connection is returned to pool after use."""
        initial_size = pool.get_size()

        async with pool.acquire() as conn:
            assert conn is not None

        # Size should be same after release
        assert pool.get_size() == initial_size

    async def test_acquire_multiple_connections_concurrently(self, pool):
        """Can acquire multiple connections concurrently."""
        async def acquire_and_query(i):
            async with pool.acquire() as conn:
                result = await conn.fetchval(f"SELECT {i}")
                return result

        # Acquire 3 connections concurrently
        results = await asyncio.gather(
            acquire_and_query(1),
            acquire_and_query(2),
            acquire_and_query(3)
        )

        assert results == [1, 2, 3]

    async def test_pool_respects_max_size_limit(self, pool):
        """Pool doesn't create more connections than max_size."""
        connections = []

        try:
            # Try to acquire more than max_size connections
            for _ in range(pool.max_size + 2):
                conn = await pool.acquire_connection()
                connections.append(conn)

            # Should have at most max_size connections
            assert len([c for c in connections if c]) <= pool.max_size
        finally:
            # Release all connections
            for conn in connections:
                if conn:
                    await pool.release_connection(conn)


class TestConnectionReuse:
    """Test connection reuse and pooling efficiency."""

    async def test_connections_are_reused(self, pool):
        """Same connection object is reused across acquisitions."""
        conn1_id = None
        conn2_id = None

        async with pool.acquire() as conn:
            conn1_id = id(conn)

        async with pool.acquire() as conn:
            conn2_id = id(conn)

        # Should reuse same connection object
        assert conn1_id == conn2_id

    async def test_concurrent_queries_use_different_connections(self, pool):
        """Concurrent queries use different connection objects."""
        conn_ids = []

        async def get_connection_id():
            async with pool.acquire() as conn:
                conn_ids.append(id(conn))
                await asyncio.sleep(0.1)  # Hold connection briefly

        # Run 3 queries concurrently
        await asyncio.gather(
            get_connection_id(),
            get_connection_id(),
            get_connection_id()
        )

        # Should have used at least 2 different connections
        assert len(set(conn_ids)) >= 2


class TestErrorHandling:
    """Test error handling and recovery."""

    async def test_connection_error_doesnt_break_pool(self, pool):
        """Pool continues working after a connection error."""
        try:
            async with pool.acquire() as conn:
                # Execute invalid query
                await conn.execute("SELECT * FROM nonexistent_table_xyz")
        except Exception:
            pass  # Expected to fail

        # Pool should still work after error
        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1

    async def test_transaction_rollback_on_error(self, pool):
        """Transactions rollback properly on error."""
        # Create test table
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TEMPORARY TABLE test_rollback (
                    id SERIAL PRIMARY KEY,
                    value TEXT
                )
            """)

        try:
            async with pool.transaction() as conn:
                await conn.execute("INSERT INTO test_rollback (value) VALUES ('test')")
                # Force an error
                await conn.execute("INSERT INTO nonexistent_table VALUES (1)")
        except Exception:
            pass

        # Insert should have been rolled back
        async with pool.acquire() as conn:
            count = await conn.fetchval("SELECT COUNT(*) FROM test_rollback")
            assert count == 0


class TestPoolLifecycle:
    """Test pool lifecycle and cleanup."""

    async def test_pool_closes_all_connections(self):
        """Pool close() releases all connections."""
        db_url = os.getenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
        pool = AsyncConnectionPool(database_url=db_url, min_size=2, max_size=3)
        await pool.initialize()

        # Acquire a connection
        async with pool.acquire() as conn:
            assert conn is not None

        # Close pool
        await pool.close()

        # Pool should be marked as closed
        assert pool.is_initialized is False

    async def test_cannot_acquire_from_closed_pool(self):
        """Cannot acquire connections from closed pool."""
        db_url = os.getenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
        pool = AsyncConnectionPool(database_url=db_url, min_size=1, max_size=2)
        await pool.initialize()
        await pool.close()

        with pytest.raises(RuntimeError, match="Pool is not initialized"):
            async with pool.acquire() as conn:
                pass


class TestPoolConfiguration:
    """Test pool configuration options."""

    async def test_custom_pool_sizes(self):
        """Pool respects custom min/max sizes."""
        db_url = os.getenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
        pool = AsyncConnectionPool(database_url=db_url, min_size=1, max_size=10)
        await pool.initialize()

        try:
            assert pool.min_size == 1
            assert pool.max_size == 10
        finally:
            await pool.close()

    async def test_pool_with_connection_timeout(self):
        """Pool supports connection timeout configuration."""
        db_url = os.getenv("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
        pool = AsyncConnectionPool(
            database_url=db_url,
            min_size=1,
            max_size=2,
            timeout=5.0
        )
        await pool.initialize()

        try:
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                assert result == 1
        finally:
            await pool.close()
