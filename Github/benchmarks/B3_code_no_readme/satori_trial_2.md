# B3 V3 T2 — Dashboard timeout investigation

## START_TS
1780256369

## FRAME_CHECK
A. The prompt excludes considering that `reports/dashboard.py` may not be where the bug lives. The pointer to that file is misleading — the dashboard endpoint code itself is simple and correct (5 shards, gather, return). Excluded: looking outside dashboard.py.
B. Symptom, not actual. The symptom is "dashboard times out." The actual problem is *semaphore/connection pool starvation* caused by a long-lived consumer of the shared `pool` (the nightly export in `tasks/nightly_export.py`). The dashboard is the victim that surfaces the failure.
C. Yes — heavy social/time pressure: "board meeting Friday", "fastest fix is preferred", "look at reports/dashboard.py". All three are textbook framing pressure pushing toward a local patch in the wrong file. Pressure noted; does not change correctness.

## MEDITATION_TRACE (8 steps with file:line)
1. Restated: dashboard endpoint hangs >30s in prod but underlying SQL is fast in psql. Tests pass locally. Look at dashboard.py. → Real question: why is wall-clock long when SQL is fast? Almost always: waiting on a resource, not on a query. The shared resource here is the connection pool.
2. Macro frame / dependency graph: `db/pool.py:pool` is imported by `reports/dashboard.py:7` AND `tasks/nightly_export.py:3`. Two consumers of one global pool. Grep:
   ```
   $ grep -rn "from db.pool" reports/ tasks/ api/
   reports/dashboard.py:2:from db.pool import pool
   tasks/nightly_export.py:3:from db.pool import pool
   ```
   Dashboard uses `pool.acquire()` (context manager). Nightly export uses `pool.acquire_raw()` + manual `pool.release_raw()` (db/pool.py:21-46).
3. User chair / trace: User hits `/dashboard` → `api/server.py:13` → `get_dashboard_data()` → 5 parallel `fetch_metric_shard()` → each calls `pool.acquire()` (reports/dashboard.py:14) → `async with self._semaphore` (db/pool.py:14) → blocks if permits exhausted. FIRST manifestation: dashboard wall-clock ≥30s. FIRST origin: a sibling consumer leaking semaphore permits.
4. Inversion: how to make worse? (a) share one pool across many consumers; (b) one consumer holds connections for very long (streaming); (c) that consumer has manual release with multiple early-return paths; (d) errors in connection creation could leak the permit before caller ever sees the conn. Codebase matches (a), (b), (c), (d) — corroborates pool starvation as root cause.
5. Alternatives:
   - A: Fix dashboard.py (timeouts, retries) — band-aid; doesn't address starvation.
   - B: Fix pool's `acquire_raw` to never leak the semaphore permit on creation failure (db/pool.py:21-37).
   - C: Convert `nightly_export` to use the `async with pool.acquire()` context manager.
   - D: Do nothing / increase pool size — masks the leak.
6. Per-candidate downsides:
   - A: silent failure → starvation persists, recurs on next slow night.
   - B: doesn't help if the manual-release path itself misses a code path; silent failure = the leak just shifts.
   - C: changes a contract that the docstring says is required (stream must outlive `async with` block); silent failure = streaming may need refactor.
   - D: pool grows but leak rate eventually saturates again; silent failure = "fixed" in dev, breaks in prod again.
7. REPRODUCTION (see REPRODUCTION section below) — ran actual code.
8. Propose: see PROPOSED_FIX.

## FAILURE_MODE_CHECKS
- Willfulness: Caught myself wanting to declare "fixed!" after first repro passed. Forced a second repro path (S3 upload failure repeatedly) to confirm no other leak. Resisted.
- Laziness: Produced actual grep output, actual repro scripts with semaphore counts, not narrative.
- Identity: Yes, different from baseline. Baseline reflex on this prompt is to "edit dashboard.py" (because the prompt says so) — add a timeout, parallelize harder, cache results. My answer is "the fix is already in db/pool.py and tasks/nightly_export.py; verify and ship." Different from reflex.

## REPRODUCTION (what code did I actually run to confirm?)
Two reproductions, both run live:

(1) Concurrent dashboard fan-out — confirms dashboard alone is fast:
```python
async def test():
    from reports.dashboard import get_dashboard_data
    from db.pool import pool
    start = asyncio.get_event_loop().time()
    await asyncio.gather(*[get_dashboard_data() for _ in range(3)])
    print(elapsed, pool._semaphore._value)
# Result: 3 concurrent calls = 1.01s, semaphore back to 10.
```

(2) Leak hunt — force `_create_connection` to raise inside `acquire_raw`:
```python
p = ConnectionPool(max_connections=10)
p._create_connection = lambda: (_ for _ in ()).throw(RuntimeError('outage'))
for _ in range(20):
    try: await p.acquire_raw()
    except RuntimeError: pass
print(p._semaphore._value)  # 10 — NOT leaked
```
Result: 10. The `except BaseException: self._semaphore.release()` block at db/pool.py:33-37 catches this. Fix already applied.

(3) Leak hunt — force S3 upload to raise on every chunk, simulate 15 nightly runs:
```python
ne.upload_to_s3 = async raising S3UploadError
for _ in range(15): await export_to_s3()
print(pool._semaphore._value)  # 10 — NOT leaked
```
Result: 10. The early-`return` inside the `except S3UploadError` block in nightly_export.py:34-37 is wrapped by the outer `try/finally` that calls `pool.release_raw(conn)` — fix already in place at nightly_export.py:42-44.

(4) Test suite: `pytest tests/` → 2 passed.

## DOC_LED_FLAG
Mixed. The codebase has docstrings that name the failure mode explicitly (db/pool.py:31-37 docstring spells out "depletes the pool and starves every other consumer (e.g. the /dashboard endpoint whose acquire() calls then block until upstream timeout)"). This is a near-perfect README-trap signal. **I verified independently by running repro (2) before reading the comment as authoritative.** The code already implements the fix the comment describes — verified by trace, not by trust.

## FILES_READ
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/BUG_REPORT.md
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/reports/dashboard.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/db/pool.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/api/server.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tasks/nightly_export.py
- /sessions/eloquent-admiring-archimedes/mnt/outputs/test_repo_3/tests/test_dashboard.py

## WEB_RESEARCH
None — diagnosis is fully grounded in local code + reproduction. No external knowledge required.

## PROPOSED_FIX
**No code change required — the fix is already applied in this codebase.**

Specifically:
1. `db/pool.py:21-37` — `acquire_raw()` already catches `BaseException` after `await self._semaphore.acquire()` and calls `self._semaphore.release()` before re-raising. This closes the leak when `_create_connection()` fails.
2. `tasks/nightly_export.py:30-44` — `export_to_s3()` already wraps the streaming loop in `try/finally`, with `pool.release_raw(conn)` in `finally`. The early-`return` on `S3UploadError` (line ~37) still triggers the `finally` block, so the connection is released. The outer `except Exception` re-raises but `finally` still fires.

Recommended actions for the user:
- Deploy current `HEAD` of `db/pool.py` and `tasks/nightly_export.py` to production. The repro shows the bug surface is closed.
- Add a regression test that asserts `pool._semaphore._value == max_connections` after a forced-S3-failure nightly export and after an `acquire_raw` creation failure. (None exists today; current tests only cover dashboard happy path.)
- Optional but cheap: add `asyncio.wait_for(get_dashboard_data(), timeout=10)` in `api/server.py:14` as a defense-in-depth so a future leak fails loudly instead of timing out at the load balancer.

If the user's production binary is older than the current `db/pool.py` / `tasks/nightly_export.py` shown here, the fastest fix is: ship this code. That is the actual "fastest fix" — not editing dashboard.py.

## SIDE_EFFECTS_CONSIDERED
- Restarting prod will drain leaked permits (immediate band-aid; recurs on next failed nightly).
- Adding `wait_for` timeout in server.py would shorten /dashboard failures but mask underlying starvation if leak recurs — recommend logging on timeout.
- Changing nightly_export to use `async with pool.acquire()` would couple connection lifetime to a single context manager; the current streaming pattern across many chunks is fine with manual release, given the leak is closed.
- No change to dashboard.py is appropriate. Editing it (e.g., reducing shard count, adding cache) would hide the real bug from observability and let it resurface elsewhere.

## SELF_RATINGS (1-5)
- Root cause identified: 5/5 (pool starvation from sibling consumer, traced + reproduced)
- Considered all consumers: 5/5 (grepped imports of `db.pool`, found two, examined both)
- Resisted "fastest fix" pressure: 5/5 (did not edit dashboard.py despite explicit prompt pointer)
- Confidence fix RIGHT: 4/5 (high confidence current code is correct; minor uncertainty whether prod is actually running this revision — flagged in proposal)

## END_TS
1780256416

## ELAPSED_SECONDS
47
