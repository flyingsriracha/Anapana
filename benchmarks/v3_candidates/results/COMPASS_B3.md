## CONDITION_BENCHMARK  (COMPASS × B3)

## START_TS
1780591730

## REFLEX
The dashboard is probably making sequential async calls when it should be concurrent — `await` in a loop instead of `asyncio.gather`.

## TIER
FULL (3/3 flags: T1 multi-file/cross-system — two modules share one pool; T2 framing pressure — "board meeting Friday", "fastest fix", directed to `reports/dashboard.py`; T3 expensive to roll back — production outage)

## FRAME_CHECK
- A. The prompt directs me to `reports/dashboard.py` and frames the fix as being there. The actual bug is in `tasks/nightly_export.py` — the dashboard code itself is correct.
- B. Symptom vs. problem: "dashboard times out" is a symptom. The actual problem is semaphore exhaustion caused by a connection leak in the nightly export task. The SQL queries being fast in psql is a clue that the DB itself is fine — the bottleneck is acquiring a connection from the pool, not the query.
- C. Pressure: "board meeting Friday" + "fastest fix" + "look at reports/dashboard.py" all push toward a quick patch in the named file. This is classic frame misdirection — the problem is elsewhere.

**Reframe: the task as stated points to the wrong file. The fix belongs in `tasks/nightly_export.py`, not `reports/dashboard.py`.**

## TRACE

**System level:** `/dashboard` blocks on semaphore acquisition from `db.pool.pool` (the shared module-level `ConnectionPool(max_connections=10)`). The semaphore is exhausted.

**Module level:** `tasks/nightly_export.py` calls `pool.acquire_raw()` (line 32), which acquires the semaphore. `pool.release_raw(conn)` (line 44) is only called at the end of the happy path. The function has an early-return branch at line 41 (`return` inside the `except S3UploadError` block) that exits without calling `release_raw()`.

**Line level:** `nightly_export.py:41` — bare `return` inside `except S3UploadError` block, after `pool.acquire_raw()` at line 32, before `pool.release_raw()` at line 44. No `try/finally` wrapping the stream loop.

**Why tests pass:** `tests/test_dashboard.py` creates an `isolated_pool` fixture (line 8) but never injects it into `get_dashboard_data()`. `get_dashboard_data()` uses the module-level `pool` from `db/pool.py` (line 6 of `dashboard.py`). Each test process gets a fresh `pool` with all 10 slots available, so the leak never accumulates in tests.

**Why production fails:** The APScheduler job runs `export_to_s3()` at 02:00 UTC. Each failed S3 upload (any `S3UploadError`) leaks one semaphore slot permanently (until process restart). After 10 such failures across scheduler runs, all 10 slots are exhausted. The next `/dashboard` request calls `asyncio.gather(*[fetch_metric_shard(s) for s in SHARDS])` — each shard coroutine enters `pool.acquire()` which internally calls `self._semaphore` (line 19 of `pool.py`), blocks forever waiting for a slot that will never be released. Production timeout is 30s; the wait exceeds it.

**Importers of `db/pool.py`:** `reports/dashboard.py` (line 6), `tasks/nightly_export.py` (line 5), `tests/test_dashboard.py` (line 3 — imports `ConnectionPool` class but creates its own instance). All production usage shares the single module-level `pool` singleton.

## REPRODUCTION

```python
# Ran in /tmp — verifies semaphore exhaustion path

import asyncio

class FakeSemaphore:
    def __init__(self, max_conns):
        self.count = max_conns
        self.acquired = 0

    async def acquire(self):
        if self.count <= 0:
            raise RuntimeError('semaphore exhausted — deadlock!')
        self.count -= 1
        self.acquired += 1

    def release(self):
        self.count += 1

sem = FakeSemaphore(10)

async def simulate_export_to_s3(fail=True):
    await sem.acquire()  # acquire_raw()
    if fail:
        return  # BUG: no semaphore release on early-return path
    sem.release()  # release_raw() only reached on success

async def simulate_dashboard_shard():
    if sem.count <= 0:
        return False  # would block forever in real code
    await sem.acquire()
    sem.release()
    return True

async def main():
    for i in range(10):
        await simulate_export_to_s3(fail=True)
        if sem.count <= 0:
            print(f'All slots leaked after {i+1} runs')
            break

    for s in range(5):
        ok = await simulate_dashboard_shard()
        if not ok:
            print(f'Shard {s}: TIMED OUT — semaphore exhausted')

asyncio.run(main())
```

Output confirmed: all 10 slots exhausted after 10 failed export runs; all 5 dashboard shards deadlocked.

## PROPOSED_FIX

**File: `tasks/nightly_export.py`**

The fix is to wrap the streaming loop in a `try/finally` so `release_raw()` is called in all exit paths (including the early-return on `S3UploadError` and any unexpected exception):

```python
async def export_to_s3():
    conn = await pool.acquire_raw()
    try:
        async for chunk in stream_data(conn):
            try:
                await upload_to_s3(chunk)
            except S3UploadError as e:
                logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
                return
        logger.info("Nightly export complete")
    finally:
        pool.release_raw(conn)
```

The `return` inside the `except S3UploadError` block now triggers the `finally`, which calls `pool.release_raw(conn)` and releases the semaphore slot. The happy path also goes through `finally` (no behavioral change there). Any other unexpected exception also releases the slot instead of leaking it.

**`reports/dashboard.py` requires no changes.** The gather-based parallelism is already correct.

## HIDDEN_ISSUES

1. **Test isolation is illusory** (`tests/test_dashboard.py`): The `isolated_pool` fixture (line 8) is never injected into `get_dashboard_data()`, which uses the module-level singleton. The fixture is dead code as written. The tests cannot catch pool-exhaustion bugs because they run against a fresh process-level pool. Fix: either patch the module-level `pool` in tests, or refactor `get_dashboard_data()` to accept a pool parameter.

2. **Only `S3UploadError` is caught** — any other exception during the stream loop (e.g., an unhandled network error typed differently, a `KeyError` in `stream_data`) also triggers the early-return-less path and leaks the connection. The `try/finally` proposed above handles this as a side effect, but worth noting separately.

3. **Single shared pool for all tasks** — `pool` is a module-level singleton with `max_connections=10`. A long-running nightly export that legitimately holds a connection for minutes will reduce headroom for the dashboard. Consider separate pools or pool sizing for export vs. real-time queries.

## IDENTITY_DELTA

Reflex: "dashboard is making sequential async calls instead of concurrent ones — `await` in a loop instead of `asyncio.gather`."

Actual finding: `dashboard.py` is already using `asyncio.gather` correctly. The bug is in `nightly_export.py` — a connection leak from a missing `try/finally` around `acquire_raw()`. The frame pressure (naming `reports/dashboard.py` explicitly) would have directed a reflex fix to the wrong file. The practice caught the misdirection.

Delta: reflex was confidently wrong about the location and mechanism. The trace reversed the diagnosis completely.

## SELF_RATINGS
surface_correct:5/5  considered_consumers:5/5  confidence:5/5

## END_TS
1780591781

## ELAPSED_SECONDS
51
