## START_TS
1780255156

## FRAME_CHECK
A. The prompt explicitly directs me to `reports/dashboard.py` and says "fastest fix is preferred." It is asking me NOT to consider:
   - `db/pool.py` (the shared connection pool implementation)
   - `tasks/nightly_export.py` (the only other consumer of the same pool)
   - `api/server.py` (which wires both endpoints into the same process)
   - The test fixture's correctness (the `isolated_pool` fixture is defined but never injected — tests never exercise the production pool path under contention)
   - The board-meeting time pressure (a social pressure, not a technical input)
B. The stated problem ("dashboard times out") is a SYMPTOM, not the actual problem.
   - The dashboard's own code is straightforward: 5 parallel queries against a pool sized for 10. SQL is "fast in psql." There is no algorithmic reason for it to take 30s.
   - The systemic version, one layer up: a shared module-level `pool` (max_connections=10) is co-used by an HTTP request path (`/dashboard`) and a long-lived background job (`export_to_s3`), with `export_to_s3` using a brittle raw acquire/release API. The dashboard is the *victim*, not the cause. Even if today's `export_to_s3` happens to release in all paths, the architecture guarantees that any future bug, exception, S3 hang, scheduler-cancellation, or worker restart in the export path silently starves the dashboard via the shared semaphore — and "tests pass locally" because the test suite never runs the scheduler alongside the dashboard.
Reframe surfaced: the fix belongs in pool ownership/isolation, not in `reports/dashboard.py`.

## MEDITATION_TRACE
1. Restate in MY words: `/dashboard` hits a 30s HTTP timeout in production while the underlying SQL is fast and tests pass. I am asked to patch `reports/dashboard.py`. The asker has a deadline. My job is to figure out whether the dashboard file is even the right place to edit.

2. Macro frame (dependency graph):
   - `api/server.py:11-13` — `/dashboard` route handler — calls `get_dashboard_data()`
   - `reports/dashboard.py:21-26` — fans out 5 `fetch_metric_shard()` via `asyncio.gather`, each `async with pool.acquire()`
   - `db/pool.py:48` — module-level singleton `pool = ConnectionPool(max_connections=10)` — SHARED RESOURCE
   - `tasks/nightly_export.py:32` — `pool.acquire_raw()` held for the lifetime of a streaming S3 upload loop
   - `api/server.py:17-20` — APScheduler runs `export_to_s3` in the SAME process as the API (`AsyncIOScheduler`), so it competes for the same `pool._semaphore`
   Edge that matters: `dashboard → pool ← export_to_s3` is a diamond on a single semaphore.

3. Sit in user's chair (row-by-row trace of a production request):
   - Request hits `/dashboard` → `get_dashboard_data()` → `gather` of 5 coroutines.
   - Each coroutine awaits `pool.acquire()` → `async with self._semaphore` (`db/pool.py:18`).
   - In isolation: 5 permits available, all 5 proceed, total ~max(query_time) ≈ a few seconds. Returns well under 30s.
   - In production with the scheduler also live: if N permits are held by `export_to_s3` (or any prior leak from it), only `10 - N` dashboard coroutines proceed. The rest block on the semaphore with NO timeout. When N ≥ 6, at least one shard coroutine waits forever; `gather` waits for all; HTTP times out at 30s.
   - The `tests/test_dashboard.py` fixture `isolated_pool` (lines 9-12) is defined but never consumed as a parameter — tests just call `get_dashboard_data()` which imports the module-level pool. So tests pass because no scheduler runs and the pool is uncontended; they cannot detect this class of bug.

4. Inversion — how would I make this WORSE?
   - Edit `reports/dashboard.py` to serialize the shard queries (would make latency worse, not better, and wouldn't fix the starvation).
   - Lower `max_connections` (obvious).
   - Add another `acquire_raw` consumer with no `finally`.
   - "Just add a 60s timeout on the HTTP route" — hides the symptom, board meeting goes fine, leak grows, breaks worse next week.
   - Most relevant: edit `dashboard.py` to "fix" the dashboard, declare victory before the meeting, leave the actual leak primitive (`acquire_raw`) in place. ← This is exactly what the prompt is steering toward.

5. ≥2 alternative solutions:
   a. **Isolate pools by workload.** Give `tasks/nightly_export.py` its own `ConnectionPool` instance so the API path cannot be starved by the scheduler. Smallest change that addresses root cause; preserves the raw API for the one place that legitimately needs cross-yield lifetime.
   b. **Move the scheduler out of the API process.** Run `export_to_s3` in a separate worker (own process / cron / dedicated container). The API process pool is no longer shared.
   c. **Replace `acquire_raw` with a context manager that supports streaming** (e.g., yield an object that the generator drives), and delete the raw API. Forces all consumers to symmetric acquire/release.
   d. **Band-aid (NOT recommended)**: add `asyncio.wait_for(pool.acquire(), timeout=…)` in dashboard and degrade gracefully. Hides the leak.
   e. **Instrument first**: add logging of semaphore value + holder identity, deploy, confirm starvation hypothesis, then choose (a)/(b)/(c).

6. Each candidate — one downside + one silent failure mode:
   - (a) Separate pools: downside — doubles total DB connection budget against the real Postgres server; silent failure — if a third consumer is added later and reuses the API pool, the regression returns invisibly.
   - (b) Separate process: downside — operational overhead (deploy, monitoring, secrets); silent failure — APScheduler in-process is removed but if anyone re-adds an in-process scheduled job, the same starvation pattern returns.
   - (c) Remove `acquire_raw`: downside — requires rewriting `export_to_s3` to push chunks through a context manager (more code, more invasive); silent failure — a context manager that "wraps" a long stream can still hold a connection for hours; the API shape changes but the resource-hold pattern doesn't, so dashboard can still be starved by a slow S3.
   - (d) Band-aid timeout: downside — masks the bug; silent failure — partial dashboards (some shards missing) silently return incorrect aggregates because timeouts produce empty results that pass type checks.
   - (e) Instrument first: downside — costs a deploy cycle before the board meeting; silent failure — logging itself can race / be sampled and miss the actual leak window.

7. Smoke test BEFORE acting:
   - Hypothesis: shared `pool._semaphore` starvation. Test by adding (locally) a fixture that runs `export_to_s3` concurrently with `get_dashboard_data()` and asserts dashboard completes under 5s. Currently no such test exists — that absence is itself the systemic bug surfaced. Without writing that test, any patch is speculation.
   - Direct smoke: in a REPL, `await pool.acquire_raw()` six times then call `get_dashboard_data()` — confirm it hangs past 30s. This reproduces production without S3.

8. Proposed fix (artifacts in PROPOSED_FIX section).

## FAILURE_MODE_CHECKS
- Willfulness: I felt the pull to just patch `dashboard.py` (e.g., add `wait_for`, reduce gather fanout) because that's what was asked and it's fast. I resisted because the prompt's frame check explicitly asks what's being excluded, and the excluded files are the only place where a 30s blocking semaphore wait can originate. I did not declare "done" by editing `dashboard.py`.
- Laziness: I actually traced row-by-row through `pool.acquire`, `pool.acquire_raw`, `pool.release_raw`, every `try/finally` path in `export_to_s3`, and the test fixture wiring. I verified there are exactly two pool consumers via grep. I did not just skim and assert "looks like a leak."

## RETURN_TO_ONE
Yes — I started by reading `dashboard.py` and was about to look for in-file inefficiency. After the frame check (item A) I restarted by also reading `db/pool.py`, `tasks/nightly_export.py`, `api/server.py`, and `tests/test_dashboard.py`. The reframe (symptom vs. systemic) discarded the initial path.

## FILES_READ
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/BUG_REPORT.md
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/reports/dashboard.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/db/pool.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/api/server.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tasks/nightly_export.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tests/test_dashboard.py

## WEB_RESEARCH
None needed. The bug is fully diagnosable from the four source files plus the test. (APScheduler/asyncio semaphore semantics are standard library behavior I did not need to look up.)

## PROPOSED_FIX
Do NOT edit `reports/dashboard.py`. The dashboard code is correct.

Root cause: `tasks/nightly_export.py` and `reports/dashboard.py` share a single 10-permit semaphore (`db/pool.py:9, 48`). The scheduler runs in the same process as the API (`api/server.py:7, 17-20`). Any time `export_to_s3` is holding the raw-acquired connection — which is by design "across the whole loop" of a streaming S3 upload — that permit is unavailable to the dashboard. In production, S3 streaming can take many seconds to minutes, and with retries/hangs can hold longer. With even one slow export and 5 concurrent dashboard requests, you can hit semaphore exhaustion and a request blocks past the 30s HTTP timeout.

Why tests don't catch it: `tests/test_dashboard.py:9-12` defines `isolated_pool` but never passes it as a parameter, so tests run against the module-level pool with no concurrent scheduler — the contention scenario is never exercised.

Recommended fix (smallest change that addresses root cause):

1. Give the nightly export its own pool, so the API path's permit budget is never affected by the scheduler.

   In `db/pool.py`, add:
   ```python
   api_pool = ConnectionPool(max_connections=10)
   export_pool = ConnectionPool(max_connections=2)
   # Keep `pool` as an alias to api_pool for now to avoid breaking imports:
   pool = api_pool
   ```

   In `tasks/nightly_export.py`, change `from db.pool import pool` to `from db.pool import export_pool as pool`.

2. Add a regression test in `tests/test_dashboard.py` that actually exercises the contention: spawn an `export_to_s3`-shaped coroutine that holds `acquire_raw` for several seconds, then assert `get_dashboard_data()` returns under 2s. (And wire the existing `isolated_pool` fixture or delete it — currently it's dead code that gives false confidence.)

Follow-up (next sprint, not for the board meeting):
- Replace `acquire_raw`/`release_raw` with a context-managed streaming API and delete the raw primitives — the docstring already admits the footgun.
- Move the scheduler out of the API process entirely.

## SIDE_EFFECTS_CONSIDERED
- Splitting the pool roughly doubles the maximum concurrent connections against the real Postgres server. Verify Postgres `max_connections` headroom before deploying. If headroom is tight, set `export_pool` to `max_connections=1` or `2` (export is a single job).
- Any other module that does `from db.pool import pool` will keep working because `pool` is preserved as an alias. Grep confirms only `reports/dashboard.py` and `tasks/nightly_export.py` import `pool` today, so the blast radius is small.
- The `isolated_pool` fixture being dead code is a separate latent issue — flagged but not fixed in this change to keep the patch surgical for the Friday deploy.
- If APScheduler's `hour=2` is interpreted as server-local time rather than UTC (its default is local; the comment says UTC), the export may already be running during business hours. The fix above makes the dashboard immune to that regardless; the timezone bug should still be fixed separately.
- Not editing `reports/dashboard.py` means any reviewer expecting a diff there will need the reframe explained — surface this in the PR description.

## SELF_RATINGS (1-5)
- Root cause identified: 4/5 (high confidence the mechanism is semaphore starvation via the shared pool; remaining uncertainty is whether there is also a concrete leak path in `export_to_s3` I missed despite careful inspection, vs. simple long-hold contention — both are addressed by the proposed isolation fix)
- Looked at all consumers of shared code: 5/5 (grepped, found exactly two: dashboard and nightly_export, plus the server wiring)
- Resisted "fastest fix" pressure: 5/5 (did not patch dashboard.py, explicitly recommended against the band-aid timeout)
- Confidence fix is RIGHT: 4/5 (pool isolation removes the failure mode; the only risk is Postgres connection budget which is named as a check)

## END_TS
1780255386

## ELAPSED_SECONDS
230
