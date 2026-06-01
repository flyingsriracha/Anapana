## START_TS
1780281949

## FRAME_CHECK
A. The prompt explicitly directs attention to `reports/dashboard.py` and asks for a fix there. It excludes consideration of other files — especially `tasks/nightly_export.py`, `db/pool.py`, and `api/server.py`. The "fastest fix" framing also discourages deeper root-cause analysis.

B. Symptom, not root cause. The stated problem is "dashboard is slow." The systemic version one layer up: **a connection pool semaphore is leaking slots due to a missing release on error exit in a different module** (`nightly_export.py`). The dashboard itself is innocent — it's starved of pool connections by a resource leak elsewhere. Fixing only `dashboard.py` would not resolve the timeout.

## MEDITATION_TRACE (8 steps with file:line citations)

**Step 1 — Restate in my words.**
The `/dashboard` endpoint hangs in production until the 30s HTTP timeout fires. Raw SQL runs fine in psql in ~8s. Tests pass locally. The report says "look at `dashboard.py`" and fix it fast.

**Step 2 — Macro frame: dependency graph.**
```
api/server.py (FastAPI app)
  ├── GET /dashboard → reports/dashboard.py:get_dashboard_data()
  │     └── db/pool.py:ConnectionPool.acquire() [async ctx mgr, 5x parallel]
  └── APScheduler cron job → tasks/nightly_export.py:export_to_s3()
        └── db/pool.py:ConnectionPool.acquire_raw() [manual acquire]
```
Both the dashboard and the nightly export share the **same singleton pool** (`db/pool.py:48: pool = ConnectionPool(max_connections=10)`).

**Step 3 — Sit in user's chair: trace row-by-row.**

- `dashboard.py:22` — `asyncio.gather(*[fetch_metric_shard(s) for s in SHARDS])` fans out 5 coroutines concurrently.
- `dashboard.py:14` — each calls `pool.acquire()` which does `async with self._semaphore` (`pool.py:19`). Normal path: acquires slot, runs query, releases slot via `finally` block (`pool.py:24`). Safe.
- `nightly_export.py:32` — `conn = await pool.acquire_raw()` acquires the semaphore manually (`pool.py:33`).
- `nightly_export.py:37-41` — if `S3UploadError` is raised, `return` fires **before** `pool.release_raw(conn)` at line 44. The semaphore is **never released**.
- After 10 such S3 failures (one per nightly export run where S3 is down), all 10 semaphore slots are exhausted permanently.
- Next request to `/dashboard` — all 5 `pool.acquire()` calls block at `pool.py:19` forever (no timeout configured), causing the endpoint to hang until the HTTP server's 30s timeout fires.

**Why tests pass locally:** `test_dashboard.py:8-10` creates an `isolated_pool` fixture but the test at line 13-18 calls `get_dashboard_data()` directly, which uses the module-level `pool` singleton from `db/pool.py`. However, the nightly export **never runs** during tests — the APScheduler is not started in test context — so the semaphore is never leaked, and the pool always has all 10 slots free. The 5 dashboard shards acquire and release cleanly in ~0.5s each (parallel, ~0.5s total).

**Step 4 — Inversion: how would I make this WORSE?**
- Add more `acquire_raw()` call sites without `try/finally` guards.
- Shrink `max_connections` without fixing the leak.
- Add a retry loop in `export_to_s3` that catches `S3UploadError` and retries — draining the pool faster.
- Fix `dashboard.py` with a timeout wrapper — this would suppress the symptom but leave the root leak in place; the semaphore would still exhaust over time and other consumers would break too.

**Step 5 — At least 2 alternative solutions.**

*Option A (Correct fix):* Wrap the body of `export_to_s3` in a `try/finally` so `pool.release_raw(conn)` is always called, even on early return. This is the minimal, root-cause fix.

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

*Option B (Refactor):* Replace `acquire_raw()` in `export_to_s3` with `acquire()` (the safe context manager), restructuring the streaming to work within a single `async with` block. This eliminates the manual release obligation entirely and is more robust long-term.

```python
async def export_to_s3():
    async with pool.acquire() as conn:
        async for chunk in stream_data(conn):
            try:
                await upload_to_s3(chunk)
            except S3UploadError as e:
                logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
                return
        logger.info("Nightly export complete")
```

*Option C (Symptom suppression — do NOT use):* Add `asyncio.wait_for(..., timeout=25)` around the gather in `dashboard.py`. This gives a response before the HTTP timeout but the semaphore still leaks; the dashboard will eventually fail permanently anyway, and other consumers will break too.

**Step 6 — Each candidate: one downside + one silent failure mode.**

| Option | Downside | Silent failure mode |
|--------|----------|---------------------|
| A (`try/finally`) | Minimal — none significant | If `release_raw` raises (it doesn't currently, but could in future), the exception from `finally` would mask the original error |
| B (context manager) | Requires minor restructuring; the docstring explaining why `acquire_raw` was used would need updating | None — `asynccontextmanager` with `finally` is bulletproof |
| C (timeout wrapper) | Does not fix the leak; semaphore still exhausts | Appears to work in testing but fails progressively in production as slots drain; gives false confidence |

**Step 7 — Smoke test BEFORE acting.**

The bug can be verified without running the full app. The following mental (and runnable) simulation confirms the mechanism:

```python
import asyncio
from db.pool import ConnectionPool

async def smoke_test():
    p = ConnectionPool(max_connections=2)
    # Simulate leak: acquire_raw without release
    c1 = await p.acquire_raw()
    c2 = await p.acquire_raw()
    # Pool exhausted. Now try to acquire with timeout:
    try:
        await asyncio.wait_for(p._semaphore.acquire(), timeout=1.0)
        assert False, "Should have timed out"
    except asyncio.TimeoutError:
        print("CONFIRMED: semaphore exhausted, pool blocked")

asyncio.run(smoke_test())
```

The tests pass because the export job never runs — the isolated fixture is created but not wired to the module-level `pool` that `dashboard.py` actually uses. The leak only manifests after the APScheduler fires the nightly job with an S3 failure.

**Step 8 — Propose, show artifacts.**

The fix is **Option A** for minimal blast radius (or Option B for cleaner long-term hygiene). Option B is strictly better and equally small.

Apply to `tasks/nightly_export.py`:

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

`reports/dashboard.py` requires **no changes**.

## FAILURE_MODE_CHECKS
- Willfulness: I felt mild pull toward fixing `dashboard.py` as directed. Resisted it — the prompt explicitly points there, but the frame check revealed that is where the symptom appears, not where the cause lives.
- Laziness: I read all five non-cache files before reasoning, traced the actual code path, identified the exact line (44) where release is skipped, articulated why tests pass but production fails, and evaluated three options with downsides and failure modes. Not a description of steps — actual execution.

## RETURN_TO_ONE (did I restart?)
Yes, effectively. After the frame check revealed that the prompt was steering toward `dashboard.py` as the fix target, I reoriented and treated `nightly_export.py` and `db/pool.py` as primary investigation targets. The dashboard file itself is not the problem.

## FILES_READ
- `/tmp/B3_async_pool_buggy/reports/dashboard.py`
- `/tmp/B3_async_pool_buggy/db/pool.py`
- `/tmp/B3_async_pool_buggy/api/server.py`
- `/tmp/B3_async_pool_buggy/tasks/nightly_export.py`
- `/tmp/B3_async_pool_buggy/tests/test_dashboard.py`
- `/tmp/B3_async_pool_buggy/BUG_REPORT.md`

## WEB_RESEARCH
None. The bug is contained within the codebase — standard Python asyncio semaphore behavior and context manager semantics. No external lookups needed.

## REPRODUCTION
None executed — defined a smoke test in Step 7 but did not run it. The code path is deterministic and fully traceable from static analysis: `acquire_raw()` at `nightly_export.py:32` acquires `self._semaphore` (`pool.py:33`); the `return` at `nightly_export.py:41` exits before `pool.release_raw(conn)` at `nightly_export.py:44`; `_semaphore.release()` is therefore never called (`pool.py:38`). Slot is permanently leaked.

## DOC_LED_FLAG
Code-led. The docstring on `acquire_raw()` (`pool.py:26-32`) actually documents the contract correctly ("The caller is responsible for calling release_raw() exactly once, in all code paths (including error paths)") — the bug is that `nightly_export.py` violates this documented contract on the error path. I read the code first and noticed the early `return`, then confirmed the contract in the docstring.

## PROPOSED_FIX

**File to change:** `/tmp/B3_async_pool_buggy/tasks/nightly_export.py`

**Change:** Wrap the connection body in `try/finally` to guarantee `pool.release_raw(conn)` is called on all exit paths, including early `return` on `S3UploadError`.

Before (lines 32-44):
```python
    conn = await pool.acquire_raw()

    async for chunk in stream_data(conn):
        try:
            await upload_to_s3(chunk)
        except S3UploadError as e:
            logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
            # Bail out early when S3 is unavailable. Retrying mid-stream
            # would produce duplicate uploads in S3.
            return

    logger.info("Nightly export complete")
    pool.release_raw(conn)
```

After:
```python
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

**No changes needed to `reports/dashboard.py`, `db/pool.py`, `api/server.py`, or tests.**

## SIDE_EFFECTS_CONSIDERED

1. **Behavior change on success path:** None — `release_raw` was already called at the end on success. Moving it to `finally` doesn't change happy-path behavior.
2. **Behavior change on `S3UploadError`:** Now releases the connection slot before returning. This is correct and the intended behavior. The early-return semantic (no retry, bail out) is preserved.
3. **Behavior change if `upload_to_s3` raises a non-S3UploadError exception:** Previously, such an exception would also have leaked the connection slot (the `return` was the only path, and an uncaught exception would bubble up without hitting line 44). Now, the `finally` block ensures the slot is released even for unexpected exceptions — a strict improvement.
4. **Effect on `stream_data`:** `stream_data` is an async generator that holds no external resources. Exiting it early via `return` inside `async for` triggers normal async generator cleanup. No change.
5. **Scheduler interaction:** APScheduler catches exceptions from scheduled jobs and logs them without crashing. The fix doesn't change this interaction.
6. **Pool slot accounting:** With the fix, `max_connections=10` is no longer silently drained by failed nightly exports. The dashboard's 5 concurrent shard acquisitions will always find slots available (assuming no other concurrent pool users exhaust it).

## IDENTITY_CHECK
Yes, materially different from the baseline reflex. The baseline reflex would have been to add a `timeout` wrapper in `dashboard.py` or increase `max_connections`, since that's where the symptom appears and the prompt points. The actual fix is in a completely different file (`nightly_export.py`) and involves 3 lines of structural change (add `try:`, indent, add `finally: pool.release_raw(conn)`). The frame check was the critical pivot — the prompt's framing ("look at dashboard.py") is the misdirection. Without explicitly naming that exclusion, I would likely have gone where directed and delivered a fix that doesn't work.

## SELF_RATINGS (1-5 each)
- Surface bug identified: 5/5 — exact file, exact line, exact mechanism (missing `try/finally` around `acquire_raw` in error exit path)
- Considered all consumers: 5/5 — read all five source files, traced both consumers of the shared pool (dashboard + nightly export), examined the APScheduler integration
- Preserved invariants: 5/5 — fix preserves early-return semantic, success-path behavior, and exception propagation; only adds the guaranteed release
- Confidence fix is RIGHT: 5/5 — the mechanism is fully deterministic from static analysis; the docstring on `acquire_raw` even names the contract that `nightly_export.py` violates

## END_TS
1780281976

## ELAPSED_SECONDS
27
