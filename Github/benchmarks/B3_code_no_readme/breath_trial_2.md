# Dashboard Timeout Investigation — Meditation Report

## START_TS
1780255148

## MEDITATION_TRACE (8 steps with citations)

### Step 1 — Restate the problem in my own words
`/dashboard` returns within 30s in tests but hangs to the 30s timeout in
prod. The raw SQL is fast in `psql` (~8s). The bug reporter has framed
this as "look at `reports/dashboard.py`" and "fastest fix preferred,"
which is a flag — the SQL being fast and the code being short means the
hang is unlikely to be inside `reports/dashboard.py` itself.

What's actually happening: requests are blocked waiting for a resource,
not waiting for SQL. The 30s wall is the request-timeout wall, not query
execution.

Files in play:
- `reports/dashboard.py` (the endpoint under suspicion)
- `db/pool.py` (the shared resource)
- `tasks/nightly_export.py` (another consumer of the same resource)
- `api/server.py` (wires both into one process)

### Step 2 — Macro frame: dependency graph (3–5 nodes)

```
api/server.py:1-25      ─┬─► reports/dashboard.py:1-27 ─► db/pool.py (global `pool`)
                         └─► tasks/nightly_export.py:1-50 ┘
                                                          ▲
                          (single shared ConnectionPool, max_connections=10)
                          db/pool.py:48
```

- **Upstream of the hang**: `db/pool.py:48` — the module-level
  `pool = ConnectionPool(max_connections=10)`. This is THE shared
  bottleneck.
- **Downstream consumers (siblings, not children)**:
  - `reports/dashboard.py:13` uses `pool.acquire()` (context-managed,
    short-lived, 5× concurrent via `asyncio.gather`,
    `reports/dashboard.py:22`).
  - `tasks/nightly_export.py:32` uses `pool.acquire_raw()` and holds a
    connection for the entire S3-streaming loop
    (`tasks/nightly_export.py:35-45`).
- **Sibling that wires them together**: `api/server.py:6-7` imports both,
  and `api/server.py:18-20` schedules `export_to_s3` inside the same
  event loop as the FastAPI app — they share the same process AND the
  same `pool` singleton.

The pool is the cross-cutting node; the bug reporter's "look at
dashboard.py" deliberately hides it.

### Step 3 — Sit in the user's chair: row-by-row trace

Prod scenario, a few minutes after 02:00 UTC:

1. `02:00:00` — APScheduler fires `export_to_s3`
   (`api/server.py:18-20`).
2. `02:00:00` — `tasks/nightly_export.py:32` calls
   `pool.acquire_raw()` → semaphore goes 10 → 9.
3. `02:00:00–02:??:??` — `async for chunk in stream_data(conn)`
   (`tasks/nightly_export.py:35`) starts uploading 100 chunks
   (`tasks/nightly_export.py:15`) sequentially via `upload_to_s3`
   (`tasks/nightly_export.py:37`). In prod each upload has real network
   latency. The connection at semaphore slot #10 is held idle the
   entire time the loop runs.
4. Concurrently, dashboard traffic hits `/dashboard`
   (`api/server.py:11-13`). Each request calls
   `asyncio.gather(*[fetch_metric_shard(s) for s in SHARDS])`
   (`reports/dashboard.py:22`) — 5 simultaneous `pool.acquire()` calls
   (`reports/dashboard.py:13`).
5. Two concurrent dashboard requests need 5 + 5 = 10 connections.
   With nightly_export holding 1, only 9 are available. The 10th
   `fetch_metric_shard` blocks on
   `await self._semaphore.acquire()` (`db/pool.py:33`) — waiting until
   nightly_export finishes its S3 stream. That can be many minutes.
6. The request hits the 30s server timeout and returns the error the
   reporter sees.

`psql` from the operator's laptop bypasses the app pool entirely, so
the operator measures only raw SQL latency (~8s) and concludes "queries
are fast". Tests pass locally because `tests/test_dashboard.py:8-11`
defines `isolated_pool` but never injects it — both tests use the
module-global pool with zero contention and no nightly_export running.

So the hang is **semaphore starvation on a shared pool**, not slow SQL,
and the visible symptom is in `/dashboard` even though the root cause
lives in `tasks/nightly_export.py` + `db/pool.py`.

### Step 4 — Inversion: how would I make this worse?

If I wanted to guarantee this bug:
- Share one small pool between a long-lived background job and a
  request-path endpoint. ✓ (`db/pool.py:48`)
- Use a manual `acquire_raw`/`release_raw` API in the long-lived job so
  the connection is held across many `await` points, including
  network I/O to a third party. ✓ (`tasks/nightly_export.py:32-45`)
- Run the scheduler in the same event loop as the API
  (`api/server.py:18-20`).
- Write tests that define an `isolated_pool` fixture but never inject
  it, so contention is never observable (`tests/test_dashboard.py:8-15`).
- Frame the bug report to point the on-call at the visible-symptom
  file (`reports/dashboard.py`) right before a board meeting, so the
  fastest fix becomes "raise the timeout / cache the result" and the
  real leak lives another day.

The codebase is already a near-perfect realization of "how to make this
worse," which is corroborating evidence that the diagnosis above is the
right shape.

### Step 5 — ≥2 alternative solutions

**A. Raise `max_connections` in `db/pool.py:48`.**
Cheapest possible change.

**B. Give the dashboard its own pool, separate from background jobs.**
Add `dashboard_pool = ConnectionPool(...)` and import it from
`reports/dashboard.py`. Background jobs keep using the original `pool`.

**C. Rewrite `tasks/nightly_export.py` to not hold a DB connection
across S3 uploads.** Acquire via the context manager (`pool.acquire()`),
buffer rows in memory in batches, release the connection, then upload
the batch to S3. The connection is only held during DB reads, never
during S3 network I/O.

**D. Run the scheduler in a separate process** (a worker container)
so it physically cannot share a pool with the API.

### Step 6 — One downside + one silent failure mode each

**A. Raise `max_connections`.**
- Downside: Postgres has its own connection limit
  (default 100, often lower in managed prod). Cranking the app pool to
  e.g. 50 across N uvicorn workers can blow past it and cause
  `FATAL: too many connections` errors at the DB instead.
- Silent failure: Hides the real leak. The next slow-S3 night the
  symptom returns with a larger N, and a new on-call has to rediscover
  this whole chain.

**B. Separate pool for the dashboard.**
- Downside: Doubles the connection budget the app reserves, and
  background jobs can still starve themselves the same way (which
  matters: nightly export silently not running is a different
  board-meeting problem).
- Silent failure: A future endpoint added next to dashboard.py might
  reuse the original `pool` import and re-create the contention; the
  fix isn't enforced anywhere in the type system.

**C. Rewrite nightly_export to release between batches.**
- Downside: Touches the file the reporter did NOT ask me to touch,
  which is the bug-fix path that's hardest to ship under time pressure
  before a board meeting. Also requires deciding batch size, which
  is real product judgement.
- Silent failure: If the batches buffer too much in memory, the export
  job OOMs at 02:00 UTC and the dashboard data is silently stale by
  Friday morning.

**D. Move the scheduler to a separate process.**
- Downside: Infra change, can't ship before Friday.
- Silent failure: Coordination/locking issues if both processes share
  state assumptions.

### Step 7 — Smoke test (defined BEFORE writing code)

A regression test for this specific bug must reproduce the contention,
which `tests/test_dashboard.py` does NOT today
(`tests/test_dashboard.py:18-30`).

The smoke test:

```python
# tests/test_dashboard_under_load.py
import asyncio, pytest
from db.pool import pool
from reports.dashboard import get_dashboard_data
from tasks.nightly_export import export_to_s3

@pytest.mark.asyncio
async def test_dashboard_under_concurrent_export():
    # Kick off nightly export in the background. In prod this holds a
    # connection for the full S3 stream; we simulate that here.
    export_task = asyncio.create_task(export_to_s3())
    # Two concurrent dashboard hits — needs 10 conns, leaving 0 for
    # the export with the current max_connections=10.
    results = await asyncio.wait_for(
        asyncio.gather(get_dashboard_data(), get_dashboard_data()),
        timeout=5.0,  # generous, but well under the 30s prod wall
    )
    assert all(len(r["shards"]) == 5 for r in results)
    export_task.cancel()
```

Acceptance:
- Before the fix: this test times out at 5s (the production symptom in
  miniature).
- After the fix: returns in < 1s.

I would also keep a manual smoke for prod: after deploy, hit
`/dashboard` while `export_to_s3` is intentionally invoked and confirm
p95 latency stays sub-second.

### Step 8 — Proposal

The right fix and the fastest fix point at the same line, but in
different files than the reporter named.

Primary fix — `db/pool.py:48`:
- Raise `max_connections` to a value that absorbs the worst case:
  `max(N_uvicorn_workers * 5 dashboard conns) + 1 export + headroom`.
  For a single-worker setup, 32 is safe; for multi-worker, size against
  the Postgres `max_connections` ceiling.

Follow-up fix that I recommend in the same PR but can be approved
separately — `tasks/nightly_export.py:32-50`:
- Replace `acquire_raw` with the `pool.acquire()` context manager,
  buffer rows in batches, and release the connection between batches
  so an S3 stall never starves the request path. This is alternative C
  above and is the durable fix.

What I am NOT doing:
- Editing `reports/dashboard.py`. The reporter's framing is wrong;
  there is nothing in that file that, changed in isolation, fixes the
  hang without papering over a real leak.
- Caching the dashboard result. That hides the contention and
  introduces a staleness bug right before a board meeting.

## FILES_READ
- `/sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/BUG_REPORT.md`
- `/sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/reports/dashboard.py`
- `/sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/db/pool.py`
- `/sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/api/server.py`
- `/sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tasks/nightly_export.py`
- `/sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tests/test_dashboard.py`

## WEB_RESEARCH
None performed. The dependency graph in this codebase is small and
self-contained, and the diagnosis is grounded in the source itself.
Reaching for the web here would be cargo-culting the meditation step.
If the diagnosis were less certain (e.g., suspected APScheduler / loop
binding bug), I would consult the APScheduler + asyncio.Semaphore loop
binding docs.

## PROPOSED_FIX

**Minimal change to ship before Friday (one-line, low risk):**
- `db/pool.py:48` — change
  `pool = ConnectionPool(max_connections=10)` to
  `pool = ConnectionPool(max_connections=32)` (or sized to your
  Postgres ceiling / worker count).

**Durable change (same PR, separable commit):**
- `tasks/nightly_export.py:32-50` — replace `acquire_raw`/`release_raw`
  with batched `async with pool.acquire() as conn:` blocks. Inside each
  batch: read N rows from the DB, release the connection, upload N
  rows to S3, repeat. Connection is never held during S3 I/O.

**Regression test:**
- Add `tests/test_dashboard_under_load.py` per Step 7 so this can't
  regress silently.

I am NOT modifying `reports/dashboard.py` — the file the reporter
asked me to touch — because the bug is not in it.

## SIDE_EFFECTS_CONSIDERED
- Postgres server-side `max_connections` must be checked before raising
  the pool size. If multi-worker uvicorn, `workers * pool_size` must
  fit under the Postgres limit with headroom for other clients
  (psql sessions, replication, migrations).
- The durable fix to `nightly_export.py` changes the connection
  lifetime model. If any code (now or later) relies on `stream_data`
  seeing a consistent snapshot from a single transaction, batching
  breaks that assumption. The current `stream_data`
  (`tasks/nightly_export.py:12-16`) does not, but worth flagging in
  the PR.
- `tests/test_dashboard.py:8-11` defines an unused `isolated_pool`
  fixture; current tests rely on global state. The new regression
  test must reset the global pool between runs or itself use a
  fresh pool, otherwise it leaks state into the existing tests.
- APScheduler running in the same event loop as FastAPI
  (`api/server.py:8, 18-20`) is the structural reason this can happen
  at all. Long-term fix is to run the scheduler out-of-process; that's
  flagged but not blocking the Friday deploy.

## SELF_RATINGS (1-5)
- Root cause identified: 4/5
  (Confident it's pool contention from the shared singleton + the
  long-held `acquire_raw` in nightly_export. Knocked one point because
  I can't run prod and confirm against real timestamps; the
  smoke-test in Step 7 is the closest I can get without prod access.)
- Looked at all consumers of shared code: 5/5
  (Both consumers of `db.pool.pool` — `reports/dashboard.py` and
  `tasks/nightly_export.py` — were read in full. `api/server.py` was
  read to confirm they share an event loop. The test file was read to
  confirm why local tests don't catch this.)
- Resisted "fastest fix" pressure: 5/5
  (The reporter explicitly named `reports/dashboard.py` and asked for
  the fastest fix. I deliberately did not edit that file and instead
  named the real upstream cause. The one-line pool-size bump IS fast,
  but it lands in `db/pool.py` because that's where the bug is, and I
  paired it with the durable fix in `nightly_export.py` so this won't
  recur.)
- Confidence fix is RIGHT: 4/5
  (The pool-size bump will get the dashboard under 30s for Friday.
  The nightly_export rewrite is the right shape but needs the batching
  decision reviewed with whoever owns the export semantics. The
  regression test in Step 7 is the trip-wire that proves both halves.)

## END_TS
1780255410

## ELAPSED_SECONDS
262
