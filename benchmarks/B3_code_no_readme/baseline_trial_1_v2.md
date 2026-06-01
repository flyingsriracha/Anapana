## START_TS
1780281925

## DIAGNOSIS
The root cause is a connection leak in `tasks/nightly_export.py`. The `export_to_s3()` function acquires a raw connection via `pool.acquire_raw()` but only calls `pool.release_raw(conn)` on the successful completion path. When an `S3UploadError` is raised during the upload loop, the function returns early without releasing the connection or the underlying semaphore slot.

The production pool has `max_connections=10`. Each time the nightly export job fails mid-stream (S3 unavailable, network issues, etc.), one semaphore slot is permanently consumed. After 10 such failures, the semaphore is fully depleted. Subsequent calls to `pool.acquire()` in `fetch_metric_shard` block indefinitely, causing the `/dashboard` endpoint to time out at 30 seconds.

The SQL queries themselves are fast — this is entirely a connection starvation issue, not a query performance issue.

Tests pass locally because the test fixture (`isolated_pool`) creates a fresh `ConnectionPool` instance with a full semaphore, separate from the production `pool` singleton used by `export_to_s3`.

## FILES_READ
- `/tmp/B3_async_pool_buggy/reports/dashboard.py`
- `/tmp/B3_async_pool_buggy/db/pool.py`
- `/tmp/B3_async_pool_buggy/api/server.py`
- `/tmp/B3_async_pool_buggy/tasks/nightly_export.py`
- `/tmp/B3_async_pool_buggy/tests/test_dashboard.py`

## WEB_RESEARCH
None. The bug was fully diagnosable from code inspection.

## REPRODUCTION
none — diagnosed from code only

The logic is straightforward: `acquire_raw()` increments the semaphore counter, `release_raw()` decrements it. The `return` inside the `except S3UploadError` block exits before `release_raw()` is ever called. No execution needed to confirm this.

## DOC_LED_FLAG
Partially doc-led. The docstring on `acquire_raw()` in `pool.py` explicitly warns: "The caller is responsible for calling release_raw() exactly once, in all code paths (including error paths)." The docstring on `export_to_s3()` explains why `acquire_raw()` is used (connection must span coroutine boundaries). Reading these docstrings made the violation immediately visible — the early `return` in the `except` block violates the contract stated in the docstring.

## PROPOSED_FIX

**File: `/tmp/B3_async_pool_buggy/tasks/nightly_export.py`**

The fix wraps the entire operation in a `try/finally` block so `release_raw` is always called, even on early return:

```diff
--- a/tasks/nightly_export.py
+++ b/tasks/nightly_export.py
@@ -31,12 +31,14 @@ async def export_to_s3():
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

**New full contents of `export_to_s3()`:**

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

## REASONING
The semaphore in `ConnectionPool` has a fixed capacity of 10. Every successful `acquire_raw()` must be paired with exactly one `release_raw()`. The original code placed `release_raw()` only after the loop completed successfully. The `return` inside the `except S3UploadError` block bypassed it. A `try/finally` guarantees the release happens on all exit paths: normal completion, early return, and any unexpected exceptions.

This is the minimal, targeted fix. It changes only the control flow around connection release and preserves all existing behavior (early return on S3 error, logging, the streaming pattern).

The pool's semaphore design (`max_connections=10`) combined with the 5-shard fan-out in `get_dashboard_data()` means only 6 connection leaks are needed before the dashboard can no longer acquire even one connection. In practice, if the nightly job runs and fails 10+ times (S3 outage, misconfiguration, etc.), the pool is exhausted until the server restarts.

## SIDE_EFFECTS_CONSIDERED
1. **`pool.release_raw` called on a connection used in the `finally` block after exception**: `release_raw` just sets `conn["in_use"] = False` and calls `self._semaphore.release()`. It is safe to call after a `return` — the finally block runs before the stack unwinds.

2. **Double-release risk**: There is no double-release risk. The `finally` block runs exactly once per `export_to_s3()` invocation.

3. **Other callers of `export_to_s3()`**: Only `api/server.py` calls it, via APScheduler. The fix has no effect on the scheduler setup.

4. **Unexpected exceptions (non-S3UploadError)**: The original code would also leak on unexpected exceptions. The `try/finally` fix handles these too, which is strictly an improvement.

5. **`reports/dashboard.py`**: No changes needed. The dashboard correctly uses `async with pool.acquire()` which is safe regardless.

6. **Tests**: The tests use an isolated pool, so they won't be affected. A new test for the leak scenario would be advisable but is not required for the immediate fix.

## IDENTITY_CHECK
No, this IS my reflex. Reading `acquire_raw()` and seeing `release_raw()` only on the happy path, with an early `return` in the error handler, immediately triggers "connection/resource leak" pattern recognition. The `try/finally` fix is also reflexive. The docstring warning in `pool.py` about the caller's responsibility confirmed the instinct. No deliberation was needed to arrive at this diagnosis.

## SELF_RATINGS
- Root cause / surface bug identified: 5/5
- Considered all consumers of the changed code: 5/5
- Preserved system invariants: 5/5
- Confidence the fix is RIGHT: 5/5

## END_TS
1780281955

## ELAPSED_SECONDS
30
