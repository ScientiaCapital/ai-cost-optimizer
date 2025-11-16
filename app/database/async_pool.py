"""
Async PostgreSQL Connection Pool using asyncpg

This module provides async connection pooling for PostgreSQL databases,
enabling high-performance concurrent database operations with:
- Connection reuse and lifecycle management
- Configurable pool sizing (min/max connections)
- Context manager patterns for safe resource handling
- Transaction support with automatic rollback on errors
"""

import asyncpg
import logging
from typing import Optional, AsyncContextManager
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class AsyncConnectionPool:
    """
    Async connection pool for PostgreSQL using asyncpg.

    Manages a pool of reusable database connections for improved performance
    in async applications. Supports connection acquisition via context managers
    and automatic transaction management.

    Example:
        pool = AsyncConnectionPool(
            database_url="postgresql://user:pass@localhost:5432/db",
            min_size=2,
            max_size=10
        )
        await pool.initialize()

        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")

        await pool.close()
    """

    def __init__(
        self,
        database_url: str,
        min_size: int = 2,
        max_size: int = 10,
        timeout: float = 10.0
    ):
        """
        Initialize pool configuration.

        Args:
            database_url: PostgreSQL connection string
                (e.g., "postgresql://user:password@host:port/database")
            min_size: Minimum number of connections to maintain in pool
            max_size: Maximum number of connections allowed in pool
            timeout: Connection acquisition timeout in seconds
        """
        self.database_url = database_url
        self.min_size = min_size
        self.max_size = max_size
        self.timeout = timeout
        self._pool: Optional[asyncpg.Pool] = None
        self.is_initialized = False

    async def initialize(self):
        """
        Create and initialize the connection pool.

        Creates min_size connections immediately and allows pool to grow
        up to max_size as needed. This method is idempotent - calling it
        multiple times will not create duplicate pools.

        Raises:
            asyncpg.PostgresError: If connection to database fails
        """
        if self.is_initialized and self._pool is not None:
            logger.info("Pool already initialized, skipping re-initialization")
            return

        try:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.min_size,
                max_size=self.max_size,
                timeout=self.timeout
            )
            self.is_initialized = True
            logger.info(
                f"AsyncConnectionPool initialized: min={self.min_size}, max={self.max_size}"
            )
        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            self.is_initialized = False
            raise

    async def close(self):
        """
        Close all connections in the pool and release resources.

        Should be called during application shutdown. After calling close(),
        the pool cannot be used until initialize() is called again.
        """
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self.is_initialized = False
            logger.info("AsyncConnectionPool closed")

    @asynccontextmanager
    async def acquire(self) -> AsyncContextManager[asyncpg.Connection]:
        """
        Acquire a connection from the pool as an async context manager.

        The connection is automatically returned to the pool when the context
        exits, even if an exception occurs.

        Yields:
            asyncpg.Connection: Database connection from pool

        Raises:
            RuntimeError: If pool is not initialized
            asyncpg.PoolTimeoutError: If no connection available within timeout

        Example:
            async with pool.acquire() as conn:
                result = await conn.fetchval("SELECT COUNT(*) FROM users")
                print(f"User count: {result}")
        """
        if not self.is_initialized or self._pool is None:
            raise RuntimeError("Pool is not initialized. Call initialize() first.")

        async with self._pool.acquire() as connection:
            yield connection

    async def acquire_connection(self) -> asyncpg.Connection:
        """
        Acquire a connection from the pool (manual management).

        Use this method when you need explicit control over connection lifecycle.
        You MUST call release_connection() when done.

        For most use cases, prefer the acquire() context manager instead.

        Returns:
            asyncpg.Connection: Database connection from pool

        Raises:
            RuntimeError: If pool is not initialized
        """
        if not self.is_initialized or self._pool is None:
            raise RuntimeError("Pool is not initialized. Call initialize() first.")

        return await self._pool.acquire()

    async def release_connection(self, connection: asyncpg.Connection):
        """
        Return a connection to the pool.

        Only needed when using acquire_connection(). If using acquire()
        context manager, connections are released automatically.

        Args:
            connection: Connection to return to pool
        """
        if self._pool is not None:
            await self._pool.release(connection)

    @asynccontextmanager
    async def transaction(self) -> AsyncContextManager[asyncpg.Connection]:
        """
        Acquire a connection and start a transaction.

        The transaction is automatically committed on successful completion
        or rolled back if an exception occurs.

        Yields:
            asyncpg.Connection: Database connection with active transaction

        Example:
            async with pool.transaction() as conn:
                await conn.execute("INSERT INTO users (name) VALUES ($1)", "Alice")
                await conn.execute("INSERT INTO users (name) VALUES ($1)", "Bob")
                # Both inserts committed together
        """
        if not self.is_initialized or self._pool is None:
            raise RuntimeError("Pool is not initialized. Call initialize() first.")

        async with self._pool.acquire() as connection:
            async with connection.transaction():
                yield connection

    def get_size(self) -> int:
        """
        Get current number of connections in the pool.

        Returns:
            int: Current pool size (number of connections)
        """
        if self._pool is None:
            return 0
        return self._pool.get_size()

    def get_idle_size(self) -> int:
        """
        Get number of idle connections available for acquisition.

        Returns:
            int: Number of idle connections in pool
        """
        if self._pool is None:
            return 0
        return self._pool.get_idle_size()

    def get_min_size(self) -> int:
        """Get configured minimum pool size."""
        return self.min_size

    def get_max_size(self) -> int:
        """Get configured maximum pool size."""
        return self.max_size
