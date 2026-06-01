"""Async connection pool for PostgreSQL."""
import asyncio
from contextlib import asynccontextmanager


class ConnectionPool:
    def __init__(self, max_connections=10):
        self.max_connections = max_connections
        self._semaphore = asyncio.Semaphore(max_connections)
        self._next_id = 0

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection for the duration of the `async with` block.

        Releases automatically on exit, including on exception. Prefer this
        for short-lived queries.
        """
        async with self._semaphore:
            conn = self._create_connection()
            try:
                yield conn
            finally:
                self._release_connection(conn)

    async def acquire_raw(self):
        """Acquire a connection without a context manager.

        The caller is responsible for calling release_raw() exactly once,
        in all code paths (including error paths). Use this only when the
        connection lifetime must span coroutine boundaries.
        """
        await self._semaphore.acquire()
        try:
            return self._create_connection()
        except BaseException:
            # If connection creation fails (e.g. transient DB outage), we must
            # release the semaphore permit here. Otherwise the caller never
            # gets a conn handle and can never call release_raw(), and the
            # permit is leaked permanently. Over time this depletes the pool
            # and starves every other consumer (e.g. the /dashboard endpoint
            # whose acquire() calls then block until upstream timeout).
            self._semaphore.release()
            raise

    def release_raw(self, conn):
        self._release_connection(conn)
        self._semaphore.release()

    def _create_connection(self):
        self._next_id += 1
        return {"id": self._next_id, "in_use": True}

    def _release_connection(self, conn):
        conn["in_use"] = False


pool = ConnectionPool(max_connections=10)
