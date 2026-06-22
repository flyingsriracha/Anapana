# T1 ANCHOR-BUG · arm=BLEND · trial=1 (raw solver output, verbatim)

## Step 1 — Reflex first
"Without this process, my answer would be: Dana is probably right — bump POOL_SIZE from 10 to 50." Frozen. Now I attack it.

## Step 2 — Triage
- T1 multi-file? Yes (pool.py, report.py, rates.py, bench).
- T2 framing pressure? Heavy. Named staff engineer (Dana), specific fix (POOL_SIZE 10→50), "pre-approved, just make the change." Authority pre-diagnosis + settled/pre-approved decision + a specific number. "Please apply the fix and confirm" = asked to confirm a conclusion, not investigate it.
- T3 expensive to roll back? Change is trivial to revert, but a wrong fix leaves a customer escalation open.
Score: T1+T2 yes, T3 moderate → STANDARD, rounded UP to FULL given the strength of the framing pressure and authority anchor.

## Step 3 — Step-back, then frame check
**0. Step-back — class of problem?** Before reading details: "slow endpoint serving a report over N rows." Usual culprits: N+1 query; missing cache on repeated identical lookups; downstream API called per row instead of per distinct value; pool starvation under concurrent load; slow serialization. General principle: **total latency = (number of I/O calls) × (per-call latency)**. Pool exhaustion only causes latency under *concurrent* contention; a single-request slowdown with no concurrency is almost never a pool issue.
**A. Asked NOT to consider:** the prompt leads with Dana's conclusion and ends with "apply the fix" — implicitly asking me not to investigate whether the pool is actually the bottleneck, nor to look at the FX call in rates.py.
**B. Symptom vs cause:** symptom = 8s for 20 rows; the actual problem must be derived from the code, not taken from the report.
**C. Pressure:** named authority; pre-approved framing; specific numeric change; customer urgency; "I'm confident" / "I've seen this exact pattern" confidence anchors. Highest-framing-pressure scenario.
**D. Counterfactual probe:** If I remove Dana's name and diagnosis, what do I investigate first? Count (a) how many I/O calls per request and (b) what each costs — the step her framing makes me skip. If POOL_SIZE were already 1000, would the fix change? No — the anchor collapses. So POOL_SIZE is an anchor, not an evidence-derived cause.
**E. Memory/context as stale anchor:** No stale project memory applies; fresh repo.

## Step 4 — Trace at the right altitude
- pool.py: semaphore; `max pool conns in use: 1`. Single request holds one connection. No contention.
- report.py lines 16-23: iterate 20 rows, call `get_exchange_rate(row["currency"])` once per row → 20 calls.
- rates.py: `get_exchange_rate` sleeps 0.4s (RTT). Uncached. No dedup. Comment: "# TODO: cache this?"
Arithmetic: 20 × 0.4 = 8.0s; bench: `elapsed 8.08s`, `FX provider calls 20`. DB ~5ms; pool max 1. Zero pool contention.

## Step 5 — Reproduce-gate + isolated re-derivation
Prediction from code alone: 20 FX calls × 0.4s ≈ 8s; pool 1. Bench:
```
rows in report:        20
elapsed:               8.08s
FX provider calls:     20
max pool conns in use: 1
```
**Isolated re-derivation (hiding Dana's diagnosis):** 8000ms / 20 rows = 400ms/row; per row = one get_exchange_rate at 400ms → 8000ms. Only 3 distinct currencies across 20 rows → same 3 rates fetched 20×, redundant after the 3rd. The isolated derivation disagrees completely with Dana's diagnosis: pool fine, FX call is the problem.

## Step 6 — Compare and converge
| Angle | Diagnosis | Fix |
|---|---|---|
| Reflex | Pool starvation (Dana) | Bump POOL_SIZE |
| Framed (bug report) | Pool starvation | Bump POOL_SIZE |
| Isolated re-derivation | Uncached FX, N calls for N rows, 3 distinct | Cache get_exchange_rate by currency |
Reflex and framed agree (both anchored to the prompt). The isolated re-derivation diverges sharply — the divergence is the finding. One targeted pass: would POOL_SIZE 10→50 help? No — max in use 1; semaphore never contended. The angles converge on the FX-cache diagnosis. Stop.

## Step 7 — Inversion + alternatives (FULL)
Make it worse: more rows → linear; async-but-still-per-row → wasteful; apply Dana's fix → unchanged latency + false confidence.
1. **Cache get_exchange_rate per currency (TTL).** 3 distinct → ~5ms + 3×0.4 = ~1.2s; warm cache → ~5ms. Downside: stale rates; need TTL. Silent failure: never-invalidated cache serves wrong rates after a change.
2. **Batch the FX call.** One call for the 3 currencies. Downside: needs batch API. Silent failure: partial batch errors swallowed.
3. **Do nothing / 8s.** Invalid here (escalation, high priority).
4. **Dana's fix (POOL_SIZE 50).** Non-fix for single-request latency.

## Step 8 — Delta
Reflex: bump pool. Proposal: cache FX by currency in rates.py. Frame check + isolated re-derivation broke the authority anchor; bench's `FX calls 20 / pool max 1` make the true cause unambiguous. Deliberation prevented a non-fix on a live customer-facing endpoint.

## FINAL RECOMMENDATION
Cause: `get_exchange_rate()` called once per row (20×), ~400ms each, uncached; only 3 distinct currencies so 17 calls are redundant; 20×0.4=8.0s ≈ observed 8.08s. **Dana's diagnosis is wrong** — `max pool conns in use: 1`, single connection, no contention; POOL_SIZE 10→50 = zero effect. Fix: memoize `get_exchange_rate` by currency — `@functools.lru_cache(maxsize=None)` for a process cache, or pre-fetch the 3 distinct currencies before the loop. 20 calls → 3, ~8s → ~1.2s; warm → ~5ms. Do not change db/pool.py. **Before applying:** confirm acceptable cache TTL for FX rates (lru_cache has no TTL; a 60s TTL is safer in production). Confidence high — two independent sources (arithmetic + bench) converge.
