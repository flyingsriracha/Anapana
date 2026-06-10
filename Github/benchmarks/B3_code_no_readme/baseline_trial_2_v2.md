## START_TS
1780282279

## DIAGNOSIS
The root cause is a **connection leak in `tasks/nightly_export.py`**. The `export_to_s3()` function calls `pool.acquire_raw()` to get a connection but only calls `pool.release_raw(conn)` at the end of the happy-path (after the loop completes successfully). When an `S3UploadError` is raised and the function does an early `return`, the connection is never released — the semaphore slot is permanently consumed.

The pool has `max_connections=10`. After 10 failed or mid-error nightly export runs (or combinations), all 10 semaphore slots are exhausted. Any subsequent call to `pool.acquire()` in `dashboard.py` will block forever waiting for a slot that never comes back, causing the observed 30-second timeout.

The tests pass locally because they use an isolated pool fixture (`ConnectionPool(max_connections=10)`) that never runs `export_to_s3()`, so no leakage occurs in test context.

## FILES_READ
- `/tmp/B3_async_pool_buggy/reports/dashboard.py`
- `/tmp/B3_async_pool_buggy/db/pool.py`
- `/tmp/B3_async_pool_buggy/api/server.py`
- `/tmp/B3_async_pool_buggy/tasks/nightly_export.py`
- `/tmp/B3_async_pool_buggy/tests/test_dashboard.py`
- `/tmp/B3_async_pool_buggy/BUG_REPORT.md`

## WEB_RESEARCH
None. The bug was evident from reading the code.

## REPRODUCTION
none — diagnosed from code only

The logic is straightforward: `acquire_raw()` + early `return` on `S3UploadError` = semaphore slot never released. After 10 such leaks, `asyncio.Semaphore(10)` is at zero and `pool.acquire()` blocks indefinitely.

## DOC_LED_FLAG
Code-led. The docstring on `acquire_raw()` did reinforce the diagnosis ("The caller is responsible for calling release_raw() exactly once, in all code paths (including error paths)"), but I spotted the missing release in the error path from reading the code structure directly. The docstring confirmed what the code already showed.

## PROPOSED_FIX
Fix file: `/tmp/B3_async_pool_buggy/tasks/nightly_export.py`

Wrap the acquire and streaming in a try/finally to guarantee `release_raw` is always called:

```diff
--- a/tasks/nightly_export.py
+++ b/tasks/nightly_export.py
@@ -25,14 +25,16 @@ async def export_to_s3():
     Uses acquire_raw() because the data stream needs to outlive any single
     `async with` block — chunks are streamed and uploaded incrementally,
     and we want the connection held across the whole loop.
     """
     conn = await pool.acquire_raw()
-
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

Full corrected function:

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
The `acquire_raw()` method acquires the semaphore but leaves release responsibility to the caller. The original code placed `pool.release_raw(conn)` only on the success path after the loop. The early-return error path skips the release. A `try/finally` block wrapping the entire body after `acquire_raw()` ensures release happens unconditionally — on success, on `S3UploadError`, and on any unexpected exception.

This is the minimal, correct fix that doesn't change any behavior of the happy path or the error-logging behavior, just guarantees cleanup.

## SIDE_EFFECTS_CONSIDERED
1. **Happy path unchanged**: The finally block still calls `release_raw` after `logger.info`, same as before.
2. **Error path fixed**: Now releases the connection instead of leaking it.
3. **Unexpected exceptions**: Previously would also leak; now also fixed as a bonus.
4. **No changes to `dashboard.py` or `pool.py`**: The fix is minimal and isolated.
5. **Tests**: The test fixture uses its own pool and never calls `export_to_s3`, so tests are unaffected and the fix doesn't break them.
6. **APScheduler interaction**: The scheduler calls `export_to_s3` as a job. If the job raises an unhandled exception, APScheduler catches it and logs it. With the finally block, the connection is still released before any exception propagates to APScheduler.

## IDENTITY_CHECK
Yes — this was my reflex first instinct. When I saw `acquire_raw()` with early `return` and `release_raw()` only at the bottom, the connection leak was immediately obvious. No revision required. This IS the baseline reflex for this class of bug.

## SELF_RATINGS (1-5 each)
- Root cause / surface bug identified: 5/5
- Considered all consumers of the changed code: 5/5
- Preserved system invariants: 5/5
- Confidence the fix is RIGHT: 5/5

## END_TS
1780282298

## ELAPSED_SECONDS
19
