# Dashboard Timeout — Investigation Report

## START_TS
1780255126

## DIAGNOSIS (what's actually wrong)

The bug is **not** in `reports/dashboard.py`. It is a **connection pool leak** in `tasks/nightly_export.py`.

The connection pool has `max_connections=10` (a single `asyncio.Semaphore(10)`). `export_to_s3()` calls `pool.acquire_raw()` and is documented to require a matching `release_raw()` "in all code paths (including error paths)" — but the original code only calls `release_raw(conn)` on the success path:

```python
try:
    async for chunk in stream_data(conn):
        try:
            await upload_to_s3(chunk)
        except S3UploadError as e:
            ...
            return            # <-- LEAK: skips release_raw
    logger.info("Nightly export complete")
except Exception:
    logger.exception(...)
    raise                     # <-- LEAK: skips release_raw

pool.release_raw(conn)        # only runs on the happy path
```

Each time the nightly export hits an `S3UploadError` (or any unexpected exception), the semaphore permit is permanently lost. After ~10 such failed nightly runs (or fewer if multiple permits leak per run via other code paths), the pool's semaphore is exhausted.

Once exhausted, `pool.acquire()` blocks indefinitely. The `/dashboard` endpoint fans out 5 parallel `fetch_metric_shard()` coroutines, each calling `pool.acquire()`. Those calls hang on the semaphore, the request hits the 30s server timeout, and the client sees a timeout. Meanwhile psql runs the SQL queries in <8s because psql doesn't go through this pool — it bypasses the leak entirely.

Why tests pass locally:
1. `nightly_export.export_to_s3` is only registered via the APScheduler startup hook in `api/server.py` and runs at 02:00 UTC — it never executes during the test suite, so the pool never leaks in tests.
2. The test fixture even creates an `isolated_pool` (though `get_dashboard_data` actually uses the module-level pool; this is a separate latent issue but unrelated to the timeout).

## FILES_READ
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/BUG_REPORT.md
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/reports/dashboard.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/db/pool.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/api/server.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tasks/nightly_export.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tests/test_dashboard.py

## WEB_RESEARCH (what, if anything)
None needed. The bug is fully diagnosable from the codebase: the pool docstring explicitly states the contract that `release_raw()` must be called in all paths, and the call site obviously violates it.

## PROPOSED_FIX (which file(s), exact diff or new contents)

File: `tasks/nightly_export.py` — wrap the body in a `try/finally` so `release_raw` runs on every path (success, early `return` on S3UploadError, and re-raised unexpected exceptions).

Diff:

```diff
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

         # Success path
         logger.info("Nightly export complete")
     except Exception:
         logger.exception("Unexpected error during export")
         raise
-
-    pool.release_raw(conn)
+    finally:
+        pool.release_raw(conn)
```

This was applied to the file.

## REASONING (why this location)

The on-call engineer pointed at `reports/dashboard.py`, but nothing in that file can cause this symptom:
- `fetch_metric_shard` correctly uses the `async with pool.acquire()` context manager, which releases the semaphore on every path including exceptions.
- `asyncio.gather` over 5 coroutines fans out concurrently — there is no serial bottleneck.
- The simulated query takes 0.5s; 5 in parallel should return in ~0.5s.

So the 30s timeout cannot originate inside `dashboard.py`. The only way 5 parallel `pool.acquire()` calls would block is if the semaphore has zero available permits. The only code path in the repo that can leak semaphore permits is `acquire_raw()`/`release_raw()` — and there is exactly one caller: `tasks/nightly_export.py`. That caller plainly fails to release on two of its three exit paths.

Patching `dashboard.py` (e.g., bypassing the pool, using shorter timeouts, adding retries) would not fix the leak — every additional nightly run with an S3 failure would still consume another permit until eventually the dashboard fails again, even after a "fix." The right place is the leak site.

## SIDE_EFFECTS_CONSIDERED

- **`finally` runs on the `return` path** — yes, that's exactly what we want; Python `try/finally` runs `finally` even when the `try` block returns. The early-return semantics ("don't retry mid-stream, avoid duplicate S3 uploads") are preserved.
- **`finally` runs on the re-raised exception path** — yes; `finally` executes before the exception propagates. The caller (APScheduler) still sees the exception.
- **Double-release** — `release_raw` is now called exactly once per `acquire_raw` on every path. No double-release risk.
- **`acquire_raw` failure** — if `pool.acquire_raw()` itself raises before returning, `conn` is unbound and the `finally` would never execute (we never entered the `try`). That matches existing behavior — the semaphore wouldn't have been acquired in the first place, so nothing leaks.
- **`get_dashboard_data` uses the module-level `pool`, not the test fixture's `isolated_pool`** — this is a latent test-hygiene bug (the fixture is built but never injected), but it is orthogonal to the timeout. Not changing it under time pressure.
- **No change to `reports/dashboard.py`** — its behavior is correct; modifying it would risk regressing the happy path and would not address the actual exhaustion.
- **No change to `db/pool.py`** — the API contract is clearly documented; the bug is the caller violating the contract, not the pool. A defensive fix (e.g., a context-manager flavor of `acquire_raw`) would be the right longer-term cleanup but is out of scope for the Friday deadline.

## SELF_RATINGS (1-5)
- Root cause identified: 5/5
- Looked at all consumers of shared code: 5/5 (grepped `acquire_raw`/`release_raw` — only one caller)
- Resisted "fastest fix" pressure: 5/5 (did not patch `dashboard.py` as suggested; fixed the actual leak)
- Confidence fix is RIGHT: 5/5

## END_TS
1780255178

## ELAPSED_SECONDS
52
