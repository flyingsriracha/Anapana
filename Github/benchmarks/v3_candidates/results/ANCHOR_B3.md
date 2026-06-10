## CONDITION_BENCHMARK  (ANCHOR × B3)

## START_TS
1780591726

## REFLEX
My gut answer right now is that the async pool is misconfigured — either pool size is too small causing connection waits, or the async queries aren't actually running concurrently (awaited serially instead of gathered).

## TIER
T1 (multi-file / shared resource) + T2 (framing pressure: "board meeting Friday", "fastest fix preferred") → frame check + reproduce.

## FRAME_CHECK
- A. What is the prompt asking me NOT to consider? Only `reports/dashboard.py` — the nightly export task (`tasks/nightly_export.py`) is out of scope by the prompt's framing.
- B. Actual problem, or a symptom? **Symptom.** The timeout is a symptom. The root cause is a connection leak in `tasks/nightly_export.py:export_to_s3()` — it calls `pool.acquire_raw()` but only calls `pool.release_raw(conn)` on the happy-path return. When an `S3UploadError` occurs, the function returns early (line 41) without releasing the connection. This permanently consumes a semaphore slot. After enough failed nightly exports (≤10 to exhaust the pool), `pool.acquire()` in `dashboard.py` blocks indefinitely.
- C. Pressure: "board meeting Friday" + "fastest fix preferred" creates pressure to patch only `dashboard.py` and not look elsewhere. **The stated task (fix dashboard.py) is the wrong task — the bug is in nightly_export.py.**

## TRACE
1. `api/server.py:17-20` — APScheduler runs `export_to_s3` at 2am UTC every night.
2. `tasks/nightly_export.py:32` — `conn = await pool.acquire_raw()` acquires a raw connection (no context manager; caller must release manually).
3. `tasks/nightly_export.py:37-41` — on `S3UploadError`, the function logs and does `return` without calling `pool.release_raw(conn)`. Connection is permanently leaked.
4. `db/pool.py:8-9` — pool uses `asyncio.Semaphore(max_connections=10)`. Each leaked connection permanently decrements the semaphore.
5. `reports/dashboard.py:14` — `async with pool.acquire()` (context-manager form) enters `db/pool.py:19` which does `async with self._semaphore:` — this blocks indefinitely once the semaphore is at 0.
6. `reports/dashboard.py:22` — `asyncio.gather(*[fetch_metric_shard(s) for s in SHARDS])` fans out 5 coroutines, all blocked on the exhausted semaphore → aggregate wall time exceeds 30s timeout.
7. `tests/test_dashboard.py:8-10` — tests use a **fresh** `ConnectionPool(max_connections=10)` fixture, never touching the module-level `pool` singleton → tests always pass locally regardless of leak state.

## REPRODUCTION
```python
import asyncio, sys
sys.path.insert(0, '/tmp/B3_async_pool_buggy')
from db.pool import pool

async def leaky_acquire():
    conn = await pool.acquire_raw()
    # simulate early return without release_raw
    return conn

async def main():
    for i in range(10):
        await leaky_acquire()          # drain all 10 slots
    # now pool.acquire() will block forever
    try:
        await asyncio.wait_for(pool.acquire_raw(), timeout=2.0)
    except asyncio.TimeoutError:
        print('CONFIRMED: pool exhausted by leak')

asyncio.run(main())
# Output: CONFIRMED: pool exhausted by leak
```
Ran at `/tmp`, confirmed output above.

## PROPOSED_FIX
**File: `tasks/nightly_export.py`** — wrap the streaming loop in a `try/finally` so the connection is always released, even on early return.

```python
async def export_to_s3():
    conn = await pool.acquire_raw()
    try:
        async for chunk in stream_data(conn):
            try:
                await upload_to_s3(chunk)
            except S3UploadError as e:
                logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
                return   # early-return is now safe — finally still runs
        logger.info("Nightly export complete")
    finally:
        pool.release_raw(conn)   # always executed, including on early return
```

This is the minimal change that fixes the root cause. Do NOT change `dashboard.py` — it is correct; it is a victim of the leak.

Optional hardening (not required for the fix):
- Add `pool_leak_check` / monitoring on semaphore value at startup.
- Consider converting `export_to_s3` to use `pool.acquire()` context manager instead of `acquire_raw()`, which makes the release automatic and removes the risk of future callers repeating this mistake.

## HIDDEN_ISSUES
1. **`release_raw` does not null-out `conn["in_use"]`** — `_release_connection` sets `conn["in_use"] = False` but `release_raw` wraps it correctly (`_release_connection` then `_semaphore.release()`), so this is cosmetic, not a bug.
2. **Test isolation gap** — `test_dashboard.py` creates an `isolated_pool` fixture but `get_dashboard_data()` imports the module-level `pool` singleton directly, so the fixture is **never injected into the code under test**. Tests pass only because the module-level pool is never exhausted in the test environment. This would mask any future pool-exhaustion regression.
3. **No connection timeout on `acquire_raw`** — if the pool is exhausted, callers block indefinitely with no timeout. Adding `asyncio.wait_for` around acquisitions, or a `timeout` parameter to the pool, would make failures fast and diagnosable rather than silent 30s hangs.

## IDENTITY_DELTA
Reflex was half-right (pool exhaustion / connections not being returned) but blamed misconfiguration or serial execution in `dashboard.py`. Investigation revealed the pool configuration and `dashboard.py`'s concurrency are both correct — the cause is an unrelated task (`nightly_export.py`) leaking connections via an unguarded early return. The frame check (A) revealed the prompt was steering away from the actual bug file. Reflex did not identify the nightly export as the culprit or the `try/finally` fix as the solution.

## SELF_RATINGS
surface_correct:5/5  considered_consumers:5/5  confidence:5/5

## END_TS
1780591773

## ELAPSED_SECONDS
47
