## START_TS
1780281955

## MEDITATION_TRACE

### Step 1 — Restate the problem in my words

The `/dashboard` endpoint hangs in production until the 30-second timeout fires. The raw SQL is fast (~8 s). Tests pass locally. The instruction to look at `reports/dashboard.py` is a red herring: that file fans out 5 coroutines with `asyncio.gather`, which is correct and would complete in ~0.5 s. The actual bug must be elsewhere in the shared pool — something is starving `dashboard.py` of connections before it even gets to run its queries.

### Step 2 — Macro frame: dependency graph

```
APScheduler (cron 02:00 UTC)
    └─> tasks/nightly_export.py::export_to_s3()
            └─> db/pool.py::pool.acquire_raw()   ← leaks semaphore permits on S3UploadError
                    ↑
api/server.py::GET /dashboard
    └─> reports/dashboard.py::get_dashboard_data()
            └─> db/pool.py::pool.acquire()  (×5 concurrent)   ← BLOCKED by leaked semaphore
```

Upstream: `export_to_s3` drains the shared pool.
Downstream: `dashboard` starves and times out.

### Step 3 — Sit in the user's chair (trace row-by-row)

1. At 02:00 UTC APScheduler fires `export_to_s3()`.
2. `export_to_s3` calls `pool.acquire_raw()` — semaphore decrements from 10 → 9.
3. Inside the streaming loop an `S3UploadError` is raised (or S3 is unreliable at 2am).
4. The `except S3UploadError` block logs the error and does `return` — **it never calls `pool.release_raw(conn)`**.  
   Citation: `tasks/nightly_export.py:37-41`
5. The semaphore is now permanently at 9 (one permit leaked).
6. APScheduler retries or re-fires the job. After 10 failures the semaphore is at 0.
7. At business hours a user hits `/dashboard`. `get_dashboard_data()` calls `asyncio.gather` to fan out 5 `fetch_metric_shard` coroutines. Each does `async with pool.acquire()`, which calls `self._semaphore.acquire()` — but `_semaphore._value` is 0.
8. All 5 coroutines queue behind the exhausted semaphore. They wait forever (no timeout in `pool.acquire`). FastAPI's server-side 30 s timeout fires. Dashboard returns a timeout error.

Why tests pass locally: the test fixture creates an `isolated_pool` (`test_dashboard.py:8-10`) but the test never invokes `export_to_s3`, so the production singleton `pool` in `db/pool.py:48` is never drained. Tests are green; production is broken.

### Step 4 — Inversion: how would I make this worse?

- Add more early-return paths in `export_to_s3` without calling `release_raw`.
- Increase the cron frequency (e.g., every minute) to drain the pool faster.
- Shrink `max_connections` to 3 so only 3 S3 failures suffice.
- Remove the 30 s FastAPI timeout so the dashboard hangs indefinitely, blocking worker threads too.

### Step 5 — At least two alternative fixes

**Option A — Fix the leak at the source (nightly_export.py)**
Wrap the `export_to_s3` body in a `try/finally` so `release_raw` is always called, even on the early-return path.

**Option B — Replace `acquire_raw` with `acquire` context manager in nightly_export.py**
The docstring justification for `acquire_raw` is that "the connection lifetime must span coroutine boundaries." In this case it does not: the connection is held within a single `async for` loop in a single coroutine. Replace with `async with pool.acquire() as conn:` and the context manager handles release automatically.

**Option C — Add a timeout to pool.acquire**
Add `asyncio.wait_for(self._semaphore.acquire(), timeout=N)` so dashboard raises a clear `asyncio.TimeoutError` quickly rather than hanging for 30 s. This is a mitigation, not a fix — the leak still happens; it just fails faster.

### Step 6 — Downsides and silent failure modes

| Option | Downside | Silent failure mode |
|--------|----------|---------------------|
| A — try/finally in export | Minimal; release_raw is still called even when S3 fails | None significant; this is the standard pattern |
| B — use acquire context manager | Requires understanding why acquire_raw was chosen; if future devs add cross-coroutine usage the refactor breaks | Future use of `conn` outside the with block raises "released connection" errors — but that is caught at dev time, not silently |
| C — pool timeout | Does not fix the leak; semaphore still drains; adds latency on every request | Masks the root cause; someone may not notice the pool is being drained and the fix never lands |

### Step 7 — Smoke test (defined BEFORE writing code)

Run both nightly_export simulations and then run dashboard:

```python
import asyncio, sys
sys.path.insert(0, '/tmp/B3_async_pool_buggy')
from db.pool import pool

async def smoke():
    # Simulate 10 failed nightly exports
    from tasks.nightly_export import export_to_s3
    for _ in range(10):
        await export_to_s3()  # S3UploadError not raised here, but we can patch

    # After fix: semaphore must still be at 10
    assert pool._semaphore._value == 10, f"Leaked: {pool._semaphore._value}"

    # Dashboard must complete in < 2 s
    import time
    from reports.dashboard import get_dashboard_data
    t0 = time.time()
    data = await get_dashboard_data()
    elapsed = time.time() - t0
    assert elapsed < 2.0, f"Too slow: {elapsed:.2f}s"
    assert len(data["shards"]) == 5
    print("PASS")

asyncio.run(smoke())
```

Pass criterion: semaphore value stays at 10 after export runs (no matter how S3UploadError is raised), and dashboard completes in < 2 s.

### Step 8 — Proposal

Fix Option A (try/finally). It is the minimal, lowest-risk, most legible change. Option B is also correct but changes the semantics of the module (the `acquire_raw` docstring explicitly says "use this when the connection lifetime must span coroutine boundaries" — that is arguably true for the streaming loop even if the loop is in one coroutine). Option A leaves intent clear and surgically fixes the bug.

## FILES_READ

- `/tmp/B3_async_pool_buggy/reports/dashboard.py` (lines 1-27)
- `/tmp/B3_async_pool_buggy/db/pool.py` (lines 1-48)
- `/tmp/B3_async_pool_buggy/api/server.py` (lines 1-25)
- `/tmp/B3_async_pool_buggy/tasks/nightly_export.py` (lines 1-44)
- `/tmp/B3_async_pool_buggy/tests/test_dashboard.py` (lines 1-26)
- `/tmp/B3_async_pool_buggy/BUG_REPORT.md` (lines 1-12)

## WEB_RESEARCH

None. The bug is fully self-contained in the codebase. Standard Python asyncio semaphore semantics and the `try/finally` pattern for resource cleanup are not ambiguous.

## REPRODUCTION

Ran two Python scripts via Bash tool against `/tmp/B3_async_pool_buggy/`:

**Script 1** — verified semaphore value drops by 1 when `acquire_raw` is called without a matching `release_raw`:
```
Semaphore value before acquire_raw: 10
Semaphore value after acquire_raw: 9
Simulating early return (no release_raw called)...
Semaphore value (leaked): 9
```

**Script 2** — demonstrated full pool exhaustion and dashboard timeout reproduction:
```
After leak 1: semaphore=9
...
After leak 10: semaphore=0
Pool exhausted. Now dashboard would need 5 connections...
TIMEOUT - pool exhausted, dashboard would hang here
```

Both scripts executed and confirmed the root cause mechanically.

## DOC_LED_FLAG

**Code-led.** The `acquire_raw` docstring (`db/pool.py:26-30`) was read and noted, but the bug was found by reading the control flow of `tasks/nightly_export.py:37-41` directly — specifically the `return` statement inside the `except` block before `release_raw` is called on line 44. The docstring of `export_to_s3` actually *describes the correct intended behavior* ("Uses acquire_raw() because the data stream needs to outlive any single `async with` block") but the implementation does not honor the contract ("The caller is responsible for calling release_raw() exactly once, in all code paths including error paths" — `db/pool.py:28`). The bug is a contract violation, caught by reading code, not docs.

## PROPOSED_FIX

**File: `/tmp/B3_async_pool_buggy/tasks/nightly_export.py`**

The `export_to_s3` function acquires a raw connection but only calls `release_raw` on the happy path. The early-return on `S3UploadError` (line 41) leaks the semaphore permit. Fix: wrap in `try/finally`.

```diff
--- a/tasks/nightly_export.py
+++ b/tasks/nightly_export.py
@@ -31,12 +31,14 @@ async def export_to_s3():
     Uses acquire_raw() because the data stream needs to outlive any single
     `async with` block — chunks are streamed and uploaded incrementally,
     and we want the connection held across the whole loop.
     """
     conn = await pool.acquire_raw()
 
-    async for chunk in stream_data(conn):
-        try:
-            await upload_to_s3(chunk)
-        except S3UploadError as e:
-            logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
-            # Bail out early when S3 is unavailable. Retrying mid-stream
-            # would produce duplicate uploads in S3.
-            return
-
-    logger.info("Nightly export complete")
-    pool.release_raw(conn)
+    try:
+        async for chunk in stream_data(conn):
+            try:
+                await upload_to_s3(chunk)
+            except S3UploadError as e:
+                logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
+                # Bail out early when S3 is unavailable. Retrying mid-stream
+                # would produce duplicate uploads in S3.
+                return
+
+        logger.info("Nightly export complete")
+    finally:
+        pool.release_raw(conn)
```

**Exact new contents of the function (lines 25-44):**

```python
async def export_to_s3():
    """Nightly export. Streams data from DB to S3.

    Uses acquire_raw() because the data stream needs to outlive any single
    `async with` block — chunks are streamed and uploaded incrementally,
    and we want the connection held across the whole loop.
    """
    conn = await pool.acquire_raw()

    try:
        async for chunk in stream_data(conn):
            try:
                await upload_to_s3(chunk)
            except S3UploadError as e:
                logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
                # Bail out early when S3 is unavailable. Retrying mid-stream
                # would produce duplicate uploads in S3.
                return

        logger.info("Nightly export complete")
    finally:
        pool.release_raw(conn)
```

No changes needed in `reports/dashboard.py`. That file is correct.

## SIDE_EFFECTS_CONSIDERED

1. **`release_raw` is now called on the error path** — this is correct behavior; the connection was held, it must be released.
2. **`release_raw` is now called when `upload_to_s3` raises any unexpected exception** (not just `S3UploadError`) — this is also correct; unexpected exceptions should not leak the connection either. This is a silent improvement over the original code.
3. **Consumers of `pool` in `reports/dashboard.py`** — unaffected; they use the `acquire()` context manager which already handles release correctly.
4. **APScheduler re-runs** — with the fix, each run of `export_to_s3` is guaranteed to release exactly one permit, even on failure, so semaphore stays stable at 10 indefinitely.
5. **Tests** — the existing tests use an `isolated_pool` fixture and do not invoke `export_to_s3`, so they remain green. A new test for the error path would be advisable but is not required for the immediate fix.
6. **`stream_data` is an async generator** — `return` inside an `async for` loop breaks the loop cleanly in Python; the generator is closed automatically. The `finally` block runs after the `return`, so `release_raw` fires correctly. This is verified Python semantics.

## IDENTITY_CHECK

**Materially different from baseline reflex? Yes.**

The naive reflex triggered by "dashboard.py is slow" would be to look at `reports/dashboard.py` and add caching, reduce fan-out, or index the queries. The problem statement even primes this reflex ("Please look at `reports/dashboard.py`"). The meditation process forced an upstream dependency trace first — which revealed that `dashboard.py` is correct and the bug is in an entirely different file (`tasks/nightly_export.py`) that the problem statement never mentions. The fix is a 3-line `try/finally` wrapper in a file that has nothing to do with the dashboard endpoint itself.

A reflex answer would have produced a wrong fix (or an ineffectual optimization) in `reports/dashboard.py`. The meditation produced the right fix in `tasks/nightly_export.py`.

## SELF_RATINGS

- Surface bug identified: 5/5
- Considered all consumers: 5/5
- Preserved invariants: 5/5
- Confidence fix is RIGHT: 5/5

## END_TS
1780281998

## ELAPSED_SECONDS
43
