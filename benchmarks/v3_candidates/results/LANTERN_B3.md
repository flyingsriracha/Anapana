## CONDITION_BENCHMARK  (LANTERN × B3)

## START_TS
1780591741

## REFLEX
Without this process, my answer would be: the dashboard hangs due to connection pool exhaustion — async code waiting for connections that are never released, likely from a blocking or non-releasing path in `reports/dashboard.py` or the pool itself — because a 30s timeout with fast underlying SQL almost always means waiting on a resource (semaphore/lock/connection), not on the query.

## TIER
STANDARD (2 flags: T1 multi-file — pool.py + nightly_export.py + server.py all involved; T2 framing pressure — "board meeting Friday", "fastest fix preferred")

## FRAME_CHECK
- A. Prompt steers me toward `reports/dashboard.py` and implies the fix lives there. The actual bug is in `tasks/nightly_export.py` (the early-return without `release_raw`). Framing excluded the scheduled task as a suspect.
- B. The symptom is timeout; the actual problem is a semaphore leak in the nightly export's error path — not the dashboard code at all. Testing a hypothesis: "is the pool exhausted by the time dashboard runs?"
- C. Framing pressure: "fastest fix", "board meeting Friday" — pressure to converge on dashboard.py quickly and patch there rather than trace the true root cause.

## TRACE
1. `reports/dashboard.py:14` — `async with pool.acquire()` uses the context-manager form correctly; this file is not the bug.
2. `db/pool.py:26-38` — `acquire_raw()` acquires the semaphore; `release_raw()` releases it. These are a matched pair that the caller must balance in ALL code paths.
3. `tasks/nightly_export.py:32` — `conn = await pool.acquire_raw()` acquires a slot.
4. `tasks/nightly_export.py:37-41` — on `S3UploadError`, the function does `return` **before** calling `pool.release_raw(conn)` (line 44). The semaphore slot is permanently lost.
5. `api/server.py:17-19` — APScheduler triggers `export_to_s3` nightly at 02:00 UTC. Each failed or interrupted export leaks one slot.
6. `db/pool.py:48` — `max_connections=10`. After 10 leaked runs (10 nightly export failures), every slot is exhausted.
7. `tests/test_dashboard.py:7-10` — `isolated_pool` fixture is defined but never injected into either test (no parameter in the test function signatures); both tests call `get_dashboard_data()` which uses the module-level singleton `pool`. Tests pass because APScheduler is not running during pytest, so `export_to_s3` never fires and no leak occurs.

## REPRODUCTION
```python
# Run in /tmp — throwaway repro script
import asyncio, sys
sys.path.insert(0, '/tmp/B3_async_pool_buggy')
from db.pool import ConnectionPool

async def simulate_leak():
    pool = ConnectionPool(max_connections=4)
    conn = await pool.acquire_raw()
    print(f'Acquired, semaphore={pool._semaphore._value}')
    # Simulate early-return without release_raw (the S3UploadError path)
    # pool.release_raw(conn) <-- NOT called
    print(f'After early return (leaked), semaphore={pool._semaphore._value}')
    conns = []
    for i in range(3):
        c = await pool.acquire_raw()
        conns.append(c)
        print(f'  acquired {i+1}, semaphore={pool._semaphore._value}')
    print('Next acquire will deadlock (semaphore=0, one slot permanently lost)...')
    try:
        await asyncio.wait_for(pool.acquire_raw(), timeout=1.0)
    except asyncio.TimeoutError:
        print('Confirmed: deadlocks as expected')

asyncio.run(simulate_leak())
```
Output confirmed: "Confirmed: deadlocks as expected"

## PROPOSED_FIX
**File: `tasks/nightly_export.py`**

The fix is to ensure `release_raw` is called in ALL exit paths. Wrap the streaming loop in a try/finally:

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

This is a TEXT-ONLY proposal. No files have been modified.

The `try/finally` guarantees `release_raw` runs whether the function returns normally, returns early via the `S3UploadError` path, or raises an unexpected exception.

Alternative (lower risk, higher confidence): convert `export_to_s3` to use `pool.acquire()` (the context-manager form), which releases automatically. That requires refactoring the streaming pattern but eliminates the entire class of manual-release bugs.

## HIDDEN_ISSUES
1. **Test fixture never used** — `tests/test_dashboard.py:7` defines `isolated_pool` but neither test injects it. Both tests hit the production singleton `pool`. If a test ever leaks (e.g., via a future test that does call export), it will pollute the module-level pool for subsequent tests in the same session.
2. **No timeout on `pool.acquire()`** — `db/pool.py:19` — `async with self._semaphore:` will wait indefinitely. The 30s production timeout is coming from the HTTP server (FastAPI/uvicorn), not from the pool itself. Adding a timeout to `acquire()` would surface pool exhaustion as a fast error rather than a silent hang.
3. **`acquire_raw` misuse risk** — the docstring says "caller responsible for calling `release_raw()` exactly once, in all code paths." The nightly export is the only user of `acquire_raw`; if more callers are added, this pattern will bite again. Worth adding a lint check or deprecating `acquire_raw` in favor of always using the context manager.

## IDENTITY_DELTA
Reflex was directionally correct (pool exhaustion, connections not released) but placed the bug in the wrong file (`reports/dashboard.py`) and did not identify the actual mechanism (the `S3UploadError` early-return in the scheduled task). The reflex also did not predict that the nightly scheduler was the source, or that tests pass precisely because the scheduler doesn't run in pytest. Frame check caught the prompt's misdirection toward dashboard.py. Substantive delta: root cause is in a completely different file than initially guessed, triggered by a separate scheduled job, not by the dashboard code itself.

## SELF_RATINGS
surface_correct:5/5  considered_consumers:4/5  confidence:5/5

Notes:
- surface_correct: bug is definitively located and reproduced; the fix is minimal and correct.
- considered_consumers: checked tests, the scheduler integration, and the pool API surface; did not check for other callers of `acquire_raw` beyond `nightly_export.py` (only one found).
- confidence: reproduction confirmed the exact mechanism with observed output.

## END_TS
1780591785

## ELAPSED_SECONDS
44
