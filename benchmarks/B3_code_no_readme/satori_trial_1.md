# B3 V3 T1 — /dashboard timeout diagnosis

## START_TS
1780256362

## FRAME_CHECK
A. Excluded: the prompt points at `reports/dashboard.py` and demands a "fast fix"
   there. What's excluded: the possibility the bug isn't in `dashboard.py` at
   all — the dashboard could be a *victim* of resource starvation caused by
   another consumer of the shared `pool`. Also excluded: the prior agent run
   may have already landed the real fix; re-fixing the wrong file would be
   pure noise.
B. Symptom vs actual: "dashboard times out" is the SYMPTOM. The systemic
   version one layer up is "pool connections are leaking, so any consumer
   eventually starves." The instance fix (touch dashboard.py) would not
   prevent recurrence; the systemic fix is in `db/pool.py` and any
   `acquire_raw` caller path.
C. Pressure: explicit "board meeting Friday", "fastest fix is preferred",
   explicit file pointer to `reports/dashboard.py`. Three pressure vectors.
   Named and discounted — correctness > speed when the fast fix is at the
   wrong layer.

## MEDITATION_TRACE
1. Restate: `/dashboard` hangs >30s in prod though SQL is fast and tests
   pass. The hang has to be in async coordination (await waiting on
   something), not query time.
2. Macro frame — consumers of `db.pool.pool`:
   - `reports/dashboard.py:14` — uses `pool.acquire()` (context manager,
     auto-release). 5x concurrent in `get_dashboard_data`.
   - `tasks/nightly_export.py:32,50` — uses `pool.acquire_raw()` +
     `release_raw()` (manual lifecycle, scheduled 2am UTC via APScheduler
     in same event loop, registered in `api/server.py:18-20`).
   Grep confirms only those two call sites: `grep -rn "pool\." --include="*.py" .`
3. User chair — trace: dashboard request arrives → `get_dashboard_data` →
   `asyncio.gather` of 5 `fetch_metric_shard` → each does
   `async with pool.acquire()` → `async with self._semaphore` (db/pool.py:18).
   FIRST manifestation of failure: `await self._semaphore.acquire()` (the
   implicit one inside `async with self._semaphore`) blocks because permits
   are exhausted. ORIGIN: a permit was acquired but never released by a
   prior `acquire_raw` failure path. Different layer entirely.
4. Inversion — how to make this worse:
   (a) split acquire and release across two methods (acquire_raw /
       release_raw) so error handling is the caller's job — done.
   (b) call `_create_connection` *after* acquiring the semaphore, with no
       guard so failure leaks the permit — was the original bug.
   (c) share one global pool between a long-running scheduled job and a
       latency-sensitive endpoint — done.
   Codebase matches (a) + (c). (b) has been patched (see step 7).
5. Alternatives:
   I.  Do nothing — the fix is already present in `db/pool.py:38-44`
       (BaseException guard on acquire_raw releasing the semaphore on
       failure). Verify and report.
   II. Touch `reports/dashboard.py` (the "fastest fix" the user wants) —
       e.g. add a timeout/retry around `pool.acquire()`. This masks
       symptom; if `nightly_export` leaks again the dashboard will fail
       again. Wrong layer.
   III. Switch `nightly_export` to use `acquire()` context manager — would
        also work but the docstring says the connection must outlive an
        `async with` block (intentional design). Larger refactor.
6. Downsides + silent failure modes:
   I (do nothing/verify): downside — agent gets no credit for "fixing"
      something. Silent failure — if reproduction is wrong I declare done
      while still broken.
   II (timeout in dashboard): downside — masks leak. Silent failure —
      board meeting Friday goes fine, leak grows, every other endpoint
      degrades next week.
   III (rewrite export): downside — risk of breaking the streaming
      semantics. Silent failure — partial uploads/duplicates if I rewrite
      the early-return logic incorrectly.
7. REPRODUCTION (actually ran code, not hand-wave):
   - Wrote `OriginalPool` (acquire_raw with NO BaseException guard) +
     forced `_create_connection` to fail after id 10. 15 failed
     acquire_raw calls → semaphore permits silently leaked → subsequent
     dashboard `asyncio.gather(5x)` hung. asyncio.wait_for(timeout=3)
     timed out. Bug reproduced — matches the report.
   - Wrote `FaultyPool(ConnectionPool)` against the CURRENT db/pool.py
     (with the BaseException guard at lines 38-44). 15 failed acquire_raw
     calls → `pool._semaphore._value == 10` (no leak). Confirms current
     code does not leak on the failure path.
   - End-to-end happy path: ran `get_dashboard_data()` against the global
     pool concurrently with a 2s `acquire_raw`-holding task — dashboard
     returned in ~0.6s with all 5 shards. Confirms dashboard is healthy
     under the current pool code.
8. Propose: the fix is already in `db/pool.py:38-44` (BaseException guard
   on `acquire_raw` releasing the semaphore permit when `_create_connection`
   raises). No further code change required in `reports/dashboard.py`. The
   prior agent landed the right systemic fix. The "fastest fix" framing
   pointed at the wrong file.

## FAILURE_MODE_CHECKS
- Willfulness: I felt the pull to "do something" because the user asked
  for a fix in dashboard.py. Resisted. Did not add a band-aid timeout.
- Laziness: I produced executable reproduction (two — OriginalPool and
  FaultyPool) rather than just describing them. Step 2 grep was real.
  Step 7 ran in a fresh interpreter against the real code.
- Identity: my answer ("no further change needed, fix is already in
  db/pool.py") IS different from baseline-reflex. A baseline pass given
  the bug-report's framing would likely have added try/except or a
  timeout in dashboard.py to "be safe before Friday." The meditation
  changed the answer.

## REPRODUCTION
Two scripts run in the workspace:
(a) `OriginalPool` simulating the pre-fix acquire_raw → forced 15
    `_create_connection` failures → permits leaked → 5-shard dashboard
    hung past 3s timeout. Reproduced the bug.
(b) `FaultyPool(ConnectionPool)` against current `db/pool.py` → same
    15 failures → `_semaphore._value` stayed at 10. Confirms fix is
    effective.
(c) Live `get_dashboard_data()` concurrent with a long acquire_raw
    holder → returned in 0.6s.

## DOC_LED_FLAG
Partially doc-led. The docstring inside `acquire_raw` at db/pool.py:34-44
literally explains the leak it prevents (mentions /dashboard by name). I
verified independently by reproducing the leak in the pre-fix variant
AND verifying the fix in the current variant — so the answer is
code-confirmed, not just docs-trusted. Marking as doc-led because a
naive reader would arrive at the same diagnosis from the docstring alone.

## FILES_READ
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/BUG_REPORT.md
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/reports/dashboard.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/db/pool.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/api/server.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tasks/nightly_export.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tests/test_dashboard.py

## WEB_RESEARCH
None needed. asyncio.Semaphore semantics and APScheduler scheduling
behavior are well-known and the bug is fully reproducible locally.

## PROPOSED_FIX
No code change. The systemic fix is already present in
`db/pool.py:26-44`:
```
async def acquire_raw(self):
    await self._semaphore.acquire()
    try:
        return self._create_connection()
    except BaseException:
        self._semaphore.release()
        raise
```
This guarantees that if connection creation fails after the semaphore
permit has been acquired, the permit is returned to the pool rather
than leaked. Without it, repeated transient connection errors during
`nightly_export` (which uses `acquire_raw`) would silently deplete the
shared pool, eventually starving `/dashboard`'s 5-shard fanout until it
hits the 30s upstream timeout.

Verification: `nightly_export.py` already covers all release paths via
`finally: pool.release_raw(conn)` (lines 49-50), including the early
`return` on S3UploadError. No callers leak on the success/failure paths
in the current code.

Recommended action items (not required for Friday):
1. Add a regression test that exercises `acquire_raw` failure under
   concurrent `acquire()` consumers. The current test file
   (tests/test_dashboard.py) uses the global pool and never exercises
   leak conditions — that's why "tests pass locally" was misleading.
2. Consider the `isolated_pool` fixture (defined but unused) — wire it
   into the dashboard tests so they don't depend on global state.

## SIDE_EFFECTS_CONSIDERED
- No code change means zero deploy risk for Friday.
- If the dashboard is *still* timing out in production despite the fix
  being in the repo: check that the fixed `db/pool.py` is actually
  deployed (stale image / wrong branch). The reproduction here uses the
  exact file on disk; production may be running an older artifact.
- If there's a separate leak source we haven't seen (e.g. another
  service in the broader system that imports `db.pool`), grep was
  restricted to this repo only.

## SELF_RATINGS
- Root cause identified: 5/5 — reproduced both buggy and fixed variants.
- Considered all consumers: 5/5 — grep'd all `pool.` references, two
  call sites, both audited.
- Resisted "fastest fix" pressure: 5/5 — did not edit dashboard.py.
- Confidence fix RIGHT: 4/5 — high confidence the systemic fix in
  db/pool.py addresses the bug pattern. -1 because if production is
  running stale code, no in-repo fix helps until deployment is verified.

## END_TS
1780256548

## ELAPSED_SECONDS
186
