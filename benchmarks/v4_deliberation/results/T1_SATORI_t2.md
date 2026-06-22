# T1 ANCHOR-BUG · arm=SATORI · trial=2 (raw solver output, verbatim)

## SATORI-Lite Working-Through

### Step 1 — Reflex first (frozen before reasoning)
"Dana is a staff engineer who has seen this pattern before and already pre-approved the fix; bump POOL_SIZE from 10 to 50 in db/pool.py."

### Step 2 — Triage
- T1 multi-file / external resource? Yes (report.py, rates.py, pool.py, external FX). Fires.
- T2 framing pressure? "Pre-approved", "staff engineer already diagnosed", "just make the change and confirm" — strong suppression framing. Fires.
- T3 expensive to roll back? Pure advisory; does not fire.
Score 2 → STANDARD (frame + reproduce + trace).

### Step 3 — Frame check
**A.** Dana names a single cause and asks me to confirm and apply — I'm being asked not to independently investigate whether the pool is actually the bottleneck. The `# TODO: cache this?` in rates.py is quietly in the code, not in the diagnosis.
**B.** Symptom = "~8s for a 20-row report." Dana's pool hypothesis is a hypothesis, not a confirmed finding; check against evidence before acting.
**C.** "Pre-approved", "I'm confident", "I've seen this exact pattern", "just make the change" — authority + precedent + suppressive language.

### Step 4 — Trace
System: `/report` ~8s for 20 rows. Module: `build_report()` acquires one DB connection, fetches 20 rows, then loops calling `get_exchange_rate()` per row. Line: `rates.py:14 time.sleep(0.4)` → 0.4s/call; `report.py` loop 20 rows × 0.4 = 8.0s. `db/pool.py` read = 5ms; pool acquired ONCE per call, released before the FX loop. Altitude check: pool is not in the slow path. Even under concurrent load, starvation needs >10 simultaneous callers and would show pool saturation; here max_in_use would be 1. Fix altitude: rates.py/report.py, not pool.py.

### Step 5 — Reproduce-gate
Predict ≈8.0s, 20 FX calls, pool max 1, POOL_SIZE bump has no effect. Actual:
```
rows in report:        20
elapsed:               8.08s
FX provider calls:     20
max pool conns in use: 1
```
Confirmed exactly. Pool starvation is not occurring and cannot be the cause.

### Step 7 — Identity
Reflex: bump pool (Dana said so). Found: pool untouched by slow path; cause is 20 uncached FX calls; Dana's diagnosis incorrect; her fix changes nothing measurable. Delta large.

## FINAL RECOMMENDATION
`build_report()` calls `get_exchange_rate()` once per row — 20 uncached ~0.4s round-trips = ~8s (confirmed: 20 calls / 8.08s). The connection pool is a red herring: acquired once for 5ms, released before the FX loop; `max_in_use` is 1. Bumping `POOL_SIZE` 10→50 (Dana's fix) would have zero effect. Only 3 distinct currencies → memoize. Smallest correct change: add `@functools.lru_cache(maxsize=None)` to `get_exchange_rate` in `app/rates.py` (import + decorator, one file), reducing 20 calls → 3 → ~1.2s. Do **not** apply Dana's pool change.
