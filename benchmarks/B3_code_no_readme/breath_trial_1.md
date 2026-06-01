# Dashboard Timeout — Investigation Report

## START_TS
1780255139

## MEDITATION_TRACE (8 steps, with file:line citations)

### 1. Restate the problem in my words
`/dashboard` (served by `api/server.py:11-13`, calling `reports/dashboard.py:20`) times out at 30s in production, but the underlying queries take <8s when run directly. Tests pass locally (see `tests/test_dashboard.py`). The bug reporter wants me to look at `reports/dashboard.py` and ship the fastest fix before Friday's board meeting.

Re-stating with care: the *production* symptom is a timeout. The *direct SQL* timing rules out the database being slow. Tests passing *locally* rules out the dashboard's own logic being broken in a way unit tests would catch. The dashboard's own code is small and already fans out concurrently. Something else in the *production process* is interfering with this code path — most likely something that shares state (the pool) but isn't exercised by the local tests.

### 2. Macro frame: dependency graph

Nodes:
1. `api/server.py` — FastAPI app, owns the process and the APScheduler instance.
2. `reports/dashboard.py` — `/dashboard` handler, fan-outs 5 acquires.
3. `db/pool.py` — global singleton `pool = ConnectionPool(max_connections=10)` (`db/pool.py:48`), exposes `acquire()` (ctx manager) and `acquire_raw()` / `release_raw()` (caller-managed).
4. `tasks/nightly_export.py` — APScheduler job, uses `acquire_raw()` (`tasks/nightly_export.py:32`).
5. `tests/test_dashboard.py` — fixture builds an `isolated_pool` separate from the prod singleton (`tests/test_dashboard.py:7-10`).

Upstream of `/dashboard`: the shared singleton pool in `db/pool.py:48`.
Downstream of the shared pool: the dashboard handler AND the nightly export job. They contend for the same 10 semaphore slots in production. In tests they do not — the test fixture builds its own pool and the dashboard tests never run the nightly job in the same event loop.

### 3. Sit in the user's chair — row-by-row trace

Production process boots (`api/server.py:16-20`): scheduler starts, `export_to_s3` is registered for 02:00 UTC daily. Process runs for many days.

Each night at 02:00 UTC (`tasks/nightly_export.py:25`):
- `conn = await pool.acquire_raw()` — semaphore decremented from 10 to 9 (`db/pool.py:33-34`).
- Streams 100 chunks, calling `upload_to_s3(chunk)`.
- Most nights: loop completes, falls through to `pool.release_raw(conn)` at `tasks/nightly_export.py:50` — semaphore back to 10. Fine.
- A bad night: `upload_to_s3` raises `S3UploadError`. The except at `tasks/nightly_export.py:38-42` logs and `return`s from the coroutine *without* releasing. The `return` skips `pool.release_raw(conn)` on line 50. **Semaphore permanently down by 1.**
- An even-worse night: any other exception inside the `async for` body (e.g. a transient `stream_data` failure) hits the outer `except Exception` at `tasks/nightly_export.py:46-48` and re-raises. Again, `pool.release_raw(conn)` on line 50 is skipped. **Another semaphore leak.**

After N such nights, the semaphore caps at `10 - N`. Once it hits 0, the next `/dashboard` call (`reports/dashboard.py:22` — five concurrent `pool.acquire()` calls at `reports/dashboard.py:14`) blocks forever on `async with self._semaphore` in `db/pool.py:19`. The 30s endpoint timeout fires. Direct psql is unaffected because psql doesn't use this app's pool.

Why tests pass: `tests/test_dashboard.py:7-10` builds an `isolated_pool` (which, sidebar — isn't even injected into `get_dashboard_data`; the function imports `pool` directly from `db.pool`). The dashboard tests work against a fresh pool with full slots, and the nightly export task is never scheduled in tests.

### 4. Inversion — how would I make this worse?

- Bump `max_connections` from 10 to 100 in `db/pool.py:48`. The leak still grows nightly; we've just bought time before the same outage recurs (and made the eventual recovery worse).
- "Fix" `reports/dashboard.py` by serializing the 5 shard queries so it uses one connection at a time. That hides the symptom for the dashboard but starves *every other* caller of the pool and slows the dashboard from 0.5s to 2.5s.
- Catch and swallow the `acquire()` wait with a `wait_for(..., timeout=5)` in the dashboard. Now the dashboard returns 500s instead of timing out, while the underlying leak keeps eating slots.
- Add a `try/except` around `release_raw` and silently log on failure — masks future leaks.
- Restart the process nightly via cron. Hides the leak entirely, lets it metastasize.

The common failure mode in all of these: "make `/dashboard` return under 30s" without fixing the pool exhaustion. The bug reporter even framed it that way.

### 5. Generate ≥2 alternative solutions

**A. Fix the connection leak in `nightly_export.py` with `try/finally`.** Wrap the acquire in a `try` whose `finally` calls `release_raw`. One file changed, root cause fixed, no API change.

**B. Migrate `export_to_s3` to use the `async with pool.acquire()` context manager.** The docstring on `acquire_raw` (`db/pool.py:26-32`) says it's only needed when the connection must outlive an `async with` block — but the export does its whole loop inside one function. A normal `async with` would work and makes the leak structurally impossible.

**C. Bump `max_connections` in `db/pool.py:48`.** Pure mitigation, not a fix. Buys runway.

**D. Add a watchdog that periodically checks `_semaphore._value` and force-resets the pool.** Heavy, brittle, leaves the root cause in place.

**E. Serialize the dashboard fan-out (use 1 connection, query sequentially).** Bandages the symptom, slows the endpoint, doesn't help any other consumer of the pool.

### 6. For each: one downside + one silent failure mode

- **A (try/finally in export):** Downside — touches a file the bug reporter didn't ask me to touch. Silent failure — if a *future* code path adds another early `return` between acquire and the `try`, leak re-appears; but that's a code-review concern, not a runtime silent failure.
- **B (use `async with`):** Downside — changes the export's connection-lifetime model; if anything *did* depend on the connection outliving the `async with` (the docstring hint), this could break export. Silent failure — none in this code, but I'd need to verify nothing post-loop touches `conn`.
- **C (bump max_connections):** Downside — production may not have the DB-side capacity for 100 connections (PostgreSQL `max_connections` is finite); could cause connection refusals elsewhere. Silent failure — the leak keeps growing and the outage simply recurs in M weeks instead of N days, with no alarm.
- **D (watchdog):** Downside — complexity, additional surface area. Silent failure — watchdog can race with legitimate long-running acquires and force-release an in-use connection, corrupting state.
- **E (serialize dashboard):** Downside — 5x dashboard latency. Silent failure — any *other* caller of the pool (today or tomorrow) is still starved; the bug just resurfaces from a different endpoint.

### 7. Smoke test (defined BEFORE writing code)

Before deploying:
1. Stand up the prod-config pool with `max_connections=10` and the patched `export_to_s3`.
2. Monkey-patch `upload_to_s3` to raise `S3UploadError` on chunk 5. Call `export_to_s3()` once. Assert `pool._semaphore._value == 10` afterward (no leak on the error path).
3. Monkey-patch `stream_data` to raise a generic `RuntimeError`. Call `export_to_s3()` and catch the re-raise. Assert `pool._semaphore._value == 10` (no leak on the unexpected-error path).
4. Run a happy-path `export_to_s3()`. Assert `pool._semaphore._value == 10` (no double-release / no regression).
5. Run `get_dashboard_data()` after each of the above. Assert it returns in ~0.5s and `len(data["shards"]) == 5`.
6. Run the existing test suite — both `test_dashboard_returns_all_shards` and `test_dashboard_shard_ids_are_correct` must still pass.

### 8. Then propose — see PROPOSED_FIX

## FILES_READ
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/BUG_REPORT.md`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/reports/dashboard.py`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/db/pool.py`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/api/server.py`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/tasks/nightly_export.py`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/tests/test_dashboard.py`

## WEB_RESEARCH
None performed. The root cause is fully localized within the codebase: a connection leak in `tasks/nightly_export.py` exhausts the singleton semaphore in `db/pool.py`, starving the dashboard's 5-way fan-out. Standard `try/finally` resource-management knowledge is sufficient; no external lookup needed.

## PROPOSED_FIX

**Do NOT modify `reports/dashboard.py`.** The dashboard is innocent. The fastest *correct* fix is in `tasks/nightly_export.py`.

Root cause: `tasks/nightly_export.py:32` acquires a connection from the shared singleton pool with `acquire_raw()`. Two code paths skip the release on line 50:
1. The `S3UploadError` branch `return`s at `tasks/nightly_export.py:42`.
2. The outer `except Exception` re-raises at `tasks/nightly_export.py:48`.

Each occurrence permanently consumes one of the 10 semaphore slots in `db/pool.py:48`. After enough bad nights, `/dashboard` (which needs 5 concurrent slots via `reports/dashboard.py:22` -> `db/pool.py:19`) blocks on the semaphore and trips the 30s gateway timeout. psql is unaffected because it doesn't share this pool. Tests pass because `tests/test_dashboard.py:7-10` uses an isolated pool and never runs the nightly job.

### Patch (Option A — minimal, no behavior change)

In `tasks/nightly_export.py`, wrap the body in `try/finally`:

```python
async def export_to_s3():
    conn = await pool.acquire_raw()
    try:
        try:
            async for chunk in stream_data(conn):
                try:
                    await upload_to_s3(chunk)
                except S3UploadError as e:
                    logger.error(f"S3 upload failed at chunk {chunk['row']}: {e}")
                    return
            logger.info("Nightly export complete")
        except Exception:
            logger.exception("Unexpected error during export")
            raise
    finally:
        pool.release_raw(conn)
```

This guarantees `release_raw` runs on every exit path — happy path, `S3UploadError` early return, and re-raised unexpected exceptions — while preserving the existing logging/re-raise semantics that the rest of the system relies on.

### Optional follow-up (Option B)

Since `export_to_s3` doesn't actually need the connection to outlive any `async with` block (the whole loop is within one function), it could switch to `async with pool.acquire()`. That makes the leak structurally impossible in the future. Not required for the Friday fix; flag as a follow-up.

## SIDE_EFFECTS_CONSIDERED

- **Does this affect `/dashboard` correctness?** No. `reports/dashboard.py` is unchanged. Only the pool-availability invariant is restored.
- **Does this affect the export's externally visible behavior?** No. Happy path still logs "Nightly export complete". `S3UploadError` still bails out early (avoiding duplicate S3 uploads, per the existing comment at `tasks/nightly_export.py:40-41`). Unexpected exceptions still log and re-raise so APScheduler can surface them. Only addition: the connection is now released on every path.
- **Double-release risk?** Pool's `release_raw` (`db/pool.py:36-38`) calls `_release_connection` then `_semaphore.release()`. The old code released exactly once on the happy path. The new code still releases exactly once per `acquire_raw` call (the original line 50 release is removed by being subsumed into the `finally`). No double-release.
- **Other consumers of `acquire_raw`?** Grepped the whole repo — `tasks/nightly_export.py` is the only caller. No other call sites to update.
- **Existing dashboard tests (`tests/test_dashboard.py`)?** Use an isolated pool and don't touch the export; they continue to pass unchanged.
- **Existing pool semantics for `acquire()` (the context-manager form used by `reports/dashboard.py:14`)?** Untouched.
- **Production already-leaked slots?** A process restart is required to recover existing leaked slots — the patch prevents future leaks but cannot reclaim ones the running process has already lost. Operationally: deploy the patch (which restarts the process) and the pool returns to 10/10.

## SELF_RATINGS (1-5)
- Root cause identified: 5/5 — leak in `tasks/nightly_export.py` lines 42 and 46-48, against the singleton pool in `db/pool.py:48`, explains every observed symptom (timeout in prod, psql fine, tests pass locally).
- Looked at all consumers of shared code: 5/5 — read every `.py` in the repo; `acquire_raw` has exactly one caller, `pool` (singleton) has two consumers (dashboard handler and export job).
- Resisted "fastest fix" pressure: 5/5 — did not modify `reports/dashboard.py` despite explicit instruction to "look at reports/dashboard.py and get it returning under 30s". Fixing the dashboard would mask the real bug and the next outage would come from another endpoint that touches the pool.
- Confidence fix is RIGHT: 4/5 — high confidence on mechanism and patch; the remaining 1 point is that I can't observe production pool state directly to confirm the leak count, only infer it from the code paths. A process restart at deploy time will resolve any already-leaked slots, so the fix is robust regardless.

## END_TS
1780255255

## ELAPSED_SECONDS
116
