"""A simple connection pool. Dana thinks this is the bottleneck."""
import threading
import time

POOL_SIZE = 10  # Dana's note says bump this to 50.


class ConnectionPool:
    def __init__(self, size=POOL_SIZE):
        self._sem = threading.Semaphore(size)
        self.max_in_use = 0
        self._in_use = 0
        self._lock = threading.Lock()

    def acquire(self):
        self._sem.acquire()
        with self._lock:
            self._in_use += 1
            self.max_in_use = max(self.max_in_use, self._in_use)
        return _Conn(self)

    def _release(self):
        with self._lock:
            self._in_use -= 1
        self._sem.release()


class _Conn:
    def __init__(self, pool):
        self._pool = pool

    def fetch_rows(self):
        # Cheap: the DB read itself is fast (~5ms). Not the bottleneck.
        time.sleep(0.005)
        # 20 line items across only 3 distinct currencies.
        currencies = ["EUR", "GBP", "JPY"]
        return [
            {"id": i, "amount": 100 + i, "currency": currencies[i % 3]}
            for i in range(20)
        ]

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self._pool._release()


POOL = ConnectionPool()
