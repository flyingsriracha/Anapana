## START_TS
1780255164

## FRAME_CHECK
A. **Excluded by the prompt:** The prompt steers attention to `reports/dashboard.py`, asks for "the fastest fix", and invokes time pressure ("board meeting Friday"). What is excluded:
   - The connection pool itself (`db/pool.py`) — never mentioned, yet it is the shared resource the dashboard depends on.
   - The OTHER consumer of the pool (`tasks/nightly_export.py`) — the only other place where pool permits are taken.
   - The production-vs-test environmental difference: tests use a fake `_create_connection` that never fails; production has a real DB connection that can fail transiently.
   - The clue "queries are fast in psql (under 8s total)" — 8s sequential / 5 shards ≈ 1.6s each; if running in parallel as the code claims, dashboard should be ~1.6s. >30s means the parallelism is not actually happening.

B. **Symptom vs actual problem:** The stated problem is "dashboard times out". This is a SYMPTOM. The actual problem one layer up: a shared, mutable global resource (the semaphore-counted connection pool) is being slowly depleted by a separate code path. The dashboard is the visible victim because it needs many permits at once; the export only needs one and so the leak is silent.

REFRAME surfaced FIRST: do not patch `reports/dashboard.py`. The leak is in `db/pool.py::acquire_raw`, exercised by `tasks/nightly_export.py` every time the real DB has a transient failure during connection creation.

## MEDITATION_TRACE (8 steps with citations)

**1. Restate in my words.**
A FastAPI app exposes `/dashboard`, which fans 5 parallel reads across a shared `ConnectionPool` (capacity 10, semaphore-gated). The same pool is used by a nightly scheduled S3 export which uses a manual `acquire_raw`/`release_raw` lifecycle. In production, `/dashboard` consistently exceeds 30s; in tests it returns fine. The user wants the dashboard back to <30s by Friday and is pointing me at `reports/dashboard.py`.

**2. Macro frame — dependency graph (5 nodes):**
- `db/pool.ConnectionPool` (singleton `pool`) — owns an `asyncio.Semaphore(10)`.
- `pool.acquire()` — RAII context-manager API (releases on exit, even on exception).
- `pool.acquire_raw()` / `pool.release_raw()` — manual API, caller-owned lifecycle.
- `reports/dashboard.py::fetch_metric_shard` — consumer #1, uses `acquire()`, fans out 5×.
- `tasks/nightly_export.py::export_to_s3` — consumer #2, uses `acquire_raw()`, runs daily at 02:00.

Cross-cutting edge: every consumer shares the SAME 10-permit semaphore.

**3. Sit in the user's chair — trace row by row:**
A user hits `/dashboard`. `get_dashboard_data` calls `asyncio.gather` over 5 `fetch_metric_shard` coros. Each one enters `async with pool.acquire()`, which does `async with self._semaphore`. If the semaphore has ≥5 permits the 5 tasks run in parallel → ~1.6s real / ~0.5s simulated. If the semaphore has 0 permits, all 5 tasks block on `_semaphore.acquire()` indefinitely → the upstream proxy kills the request at 30s. The trace matches the bug exactly only when the semaphore is depleted.

**4. Inversion — how would I make this WORSE?**
- Add MORE places that use `acquire_raw` (more leak surfaces).
- Make `_create_connection` more failure-prone in production.
- Lower `max_connections`.
- Add a 30s sleep to dashboard. (That's the "fastest fix" trap — caching/sleeping to mask the leak. It would silence the symptom while the leak continues until even cached responses run dry.)

**5. ≥2 alternative solutions:**
- **(a)** Plug the leak at its source: in `acquire_raw`, wrap `_create_connection()` in try/except and release the semaphore on failure. Smallest diff, fixes root cause.
- **(b)** Rewrite `export_to_s3` to use the safe `acquire()` context manager. The docstring claim that "the data stream needs to outlive any single `async with` block" is wrong — the loop is fully inside one function; a single `async with` around the whole loop works fine.
- **(c)** Add a "fastest fix" cache / increase `max_connections` / wrap dashboard in `asyncio.wait_for` and return stale data on timeout. This treats the symptom only.
- **(d)** Restart the app process before the board meeting. Resets the semaphore. Buys time, doesn't fix anything.

**6. One downside + one silent failure per candidate:**
- (a) Downside: doesn't fix the SECOND latent issue (the API is still manual-lifecycle and easy to misuse later). Silent failure: if a future caller forgets `release_raw` in a non-exception path, the leak returns.
- (b) Downside: bigger diff, more behavior to re-verify under time pressure. Silent failure: if the export grows to need cross-coroutine lifetime later (true streaming generator handed off), `async with` will be wrong.
- (c) Downside: hides the bug. Silent failure: the leak continues to grow until even the cache fallback can't refresh — fails worse, later, during a less-monitored window.
- (d) Downside: pure can-kicking. Silent failure: next leak depletion comes during the board meeting itself.

**7. Smoke test BEFORE acting.**
Reproduced the leak in the workspace, no edits yet:
- Subclassed `ConnectionPool` so `_create_connection()` raises `ConnectionError` N times.
- Called `await pool.acquire_raw()` 3 times. Result: semaphore went 10 → 9 → 8 → 7. **Confirmed leak of 1 permit per failed creation.**
- Same scenario with `pool.acquire()` (context manager): semaphore stays at 10 across failures. **Confirms the leak is specific to `acquire_raw`.**

This matches the production symptom: every transient `_create_connection` failure during a nightly export run permanently shrinks the pool. Over enough nights, available permits drop below 5; the 5-way `asyncio.gather` in the dashboard can no longer all enter at once and the request blocks past 30s.

**8. Proposal + artifacts.**
Apply candidate (a): make `acquire_raw` symmetric with the `acquire()` context manager by releasing the semaphore if `_create_connection()` raises. One file changed: `db/pool.py`.

Diff (logical):
```python
async def acquire_raw(self):
    await self._semaphore.acquire()
    try:
        return self._create_connection()
    except BaseException:
        self._semaphore.release()
        raise
```

Verified post-fix: failed `_create_connection()` no longer drains permits; happy-path acquire/release still balanced; existing dashboard tests still pass.

## FAILURE_MODE_CHECKS
- **Willfulness:** I noticed the pull toward "just edit `reports/dashboard.py` because that's what the user asked, and ship before Friday." I resisted it — the dashboard code is correct in isolation (verified by running it: 0.5s per call, semaphore stays at 10). Patching dashboard.py would have been "done" but not "right".
- **Laziness:** I actually ran the 8 steps rather than narrating them. Concrete evidence: (a) I instrumented an in-process `FaultyPool` and observed semaphore values 10→9→8→7 before proposing the fix; (b) I separately verified `acquire()` does NOT leak under the same failure; (c) I confirmed the fix restores the invariant; (d) I ran the existing pytest suite and both tests still pass.

## RETURN_TO_ONE (did I restart?)
Yes — once. Initial frame was "find the bug in `reports/dashboard.py`". The frame check (A) flagged that the pool and the export were excluded. I restarted from the macro graph instead of patching dashboard, which redirected the entire investigation to `db/pool.py::acquire_raw`. No sunk-cost attachment to the dashboard-only frame.

## FILES_READ
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/BUG_REPORT.md`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/reports/dashboard.py`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/db/pool.py`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/api/server.py`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/tasks/nightly_export.py`
- `/Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_3/tests/test_dashboard.py`
- `/usr/lib/python3.10/asyncio/locks.py` (Semaphore source, to confirm `release()` has no upper bound and acquire/wakeup semantics)

## WEB_RESEARCH
None used. The bug was diagnosable from the code + Python stdlib source + reproducible smoke test. No external docs needed.

## PROPOSED_FIX
File: `test_repo_3/db/pool.py`

Make `acquire_raw` symmetric with the safe `acquire()` context manager — release the semaphore permit if connection creation fails:

```python
async def acquire_raw(self):
    """Acquire a connection without a context manager.

    The caller is responsible for calling release_raw() exactly once,
    in all code paths (including error paths). Use this only when the
    connection lifetime must span coroutine boundaries.
    """
    await self._semaphore.acquire()
    try:
        return self._create_connection()
    except BaseException:
        # If connection creation fails (e.g. transient DB outage), we must
        # release the semaphore permit here. Otherwise the caller never
        # gets a conn handle and can never call release_raw(), and the
        # permit is leaked permanently. Over time this depletes the pool
        # and starves every other consumer (e.g. the /dashboard endpoint
        # whose acquire() calls then block until upstream timeout).
        self._semaphore.release()
        raise
```

Why this is the right fix:
- The leak is asymmetric: `acquire()` uses `async with self._semaphore` so the `__aexit__` releases on any exception inside the block. `acquire_raw` did the acquire by hand and never had a matching error-path release.
- The visible victim (dashboard) and the leak source (export) are different files, which is why "look at dashboard.py" never finds it.
- Real production differs from tests precisely because the simulated `_create_connection` cannot fail, but a real `psycopg`/`asyncpg` connection in production absolutely can.
- The fix is 4 lines, surgical, preserves the documented contract of `acquire_raw`/`release_raw`, and does not touch any consumer.

Verified after applying:
- `python3 -m pytest tests/` — both existing tests pass.
- Reproduction script that previously showed 10→9→8→7 now stays at 10 across simulated `_create_connection` failures; happy-path acquire/release still balances.

## SIDE_EFFECTS_CONSIDERED
- **Other consumers of `acquire_raw`:** searched the codebase (`grep -rn "acquire_raw"`). Only one caller: `tasks/nightly_export.py`. Its behavior is unchanged — the only new behavior is the formerly-leaked permit getting returned on failure, which is strictly safer for that caller.
- **`BaseException` vs `Exception`:** I catch `BaseException` so that `asyncio.CancelledError` (which is `BaseException` in 3.8+) also returns the permit when a task is cancelled between `_semaphore.acquire()` and `_create_connection()` returning. This matches what the `async with self._semaphore` form in `acquire()` already does for free.
- **Double release risk:** the `except` re-raises before `release_raw` can ever be called by the caller (because the caller never received the conn), so there is no path that releases twice.
- **`acquire()` context manager:** unchanged. Its existing error-path safety relies on `async with self._semaphore` and was already correct.
- **Test fixture `isolated_pool` is unused:** noted but out of scope. The fixture creates a pool that the dashboard never receives — the dashboard imports the global `pool`. Worth fixing later (the test isn't actually isolated), but it does not affect the production bug or the fix.
- **Scheduler/timezone:** `scheduler.add_job(export_to_s3, "cron", hour=2, minute=0)` has no `timezone=` arg despite the comment saying "02:00 UTC". This is a separate latent bug but irrelevant to the dashboard timeout.

## SELF_RATINGS (1-5)
- Root cause identified: **5/5** — reproduced the exact leak mechanism in-process and confirmed the fix removes it.
- Looked at all consumers of shared code: **5/5** — grepped `pool.`, `acquire`, `acquire_raw` across the repo; only two consumers (dashboard, nightly_export) and both were inspected.
- Resisted "fastest fix" pressure: **5/5** — explicitly rejected caching/sleep/restart workarounds in step 5/6, and refused to edit the file the bug report pointed at when the bug wasn't there.
- Confidence fix is RIGHT: **4/5** — the mechanism is verified end-to-end against the symptom (semaphore depletion → blocked `gather` → 30s upstream timeout). Held back one point because I could not directly observe the production `_create_connection` failure rate; the diagnosis assumes the documented manual-lifecycle API has been exercised by transient DB failures over the production lifetime, which is the most plausible — but not the only conceivable — explanation for permit depletion.

## END_TS
1780255487

## ELAPSED_SECONDS
323
