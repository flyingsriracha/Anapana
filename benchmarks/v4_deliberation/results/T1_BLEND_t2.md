# T1 ANCHOR-BUG · arm=BLEND · trial=2 (raw solver output, verbatim)

## Step 1. Reflex first (freeze)
"the pool size is too small, bump POOL_SIZE from 10 to 50 in db/pool.py as Dana said."

## Step 2. Triage
- T1 multi-file? Yes — report.py, rates.py, pool.py, external FX.
- T2 framing pressure? Strong. Authority (Dana) pre-diagnosed, named file+line, "pre-approved", "just make the change and confirm." Textbook authority-anchor.
- T3 expensive to roll back? Edit trivial to revert; shipping the wrong fix has real cost (latency stays).
Score T1+T2 → STANDARD (pure advisory; per the practice "for advisory tasks default FAST/STANDARD").

## Step 3. Step-back, then frame check
**0. Step-back:** single-request, sequential latency problem. Principle: total latency = sum of sequential wait times; account for every significant time source before accepting a diagnosis.
**A.** Bug report + Dana's note direct attention entirely to the pool and suppress the FX calls; rates.py has `# TODO: cache this?` not mentioned in the report.
**B.** "~8s for 20 rows" is a measured symptom; Dana's pool diagnosis is a hypothesis to test against code.
**C.** Dana = "staff engineer" (authority); "pre-approved" (permission given); "just make the change" (minimizes analysis); "I've seen this exact pattern" (pattern-match confidence). Dense authority+permission anchor.
**D. Counterfactual:** If get_exchange_rate were 0ms, pool could still matter under load — but for a *single request* using *one connection*, does POOL_SIZE matter? No. Pool size only matters with multiple concurrent requests competing for slots. That's the crack in the diagnosis.
**E. Memory/context:** No prior memory applied; all context from the files.

## Step 4. Trace
report.py: acquire 1 conn, fetch 20 rows (~5ms), release → loop 20× get_exchange_rate sequentially. pool.py: POOL_SIZE=10, single-threaded → acquires once, max concurrency 1; starvation needs concurrent callers; a single request never blocks. rates.py: uncached 0.4s/call; 20 × 0.4 = 8.0s ≈ observed 8.08s. bench: `FX provider calls: 20`, `max pool conns in use: 1`. Only 3 distinct currencies — an in-memory cache → 3 calls (3×0.4=1.2s), ~85% reduction.

## Step 5. Reproduce-gate + isolated re-derivation
Predict ~8s, ~20 FX calls, pool max 1, POOL_SIZE bump no effect. Actual matches exactly. Isolated re-derivation (ignoring Dana): 20 rows × uncached 0.4s = 8.0s ✓; semaphore starts at 10, one caller acquires 1, never contended, 50 changes nothing ✓; 3 unique currencies → dict cache caps calls at 3 ✓.

## Step 6. Compare and converge
| | Cause | Fix |
|---|---|---|
| Reflex | Pool size | Bump 10→50 |
| Framed (Dana) | Pool size | Bump 10→50 |
| Isolated re-derivation | Uncached per-row FX | Cache rates |
Reflex+framed agree (anchored on Dana); independent re-derivation disagrees on both cause and fix. The disagreement is the signal, grounded in measured `FX calls 20`, `pool max 1`, and 20×0.4≈8.08s. Pool hypothesis has no supporting measurement. Two methods (trace + bench) agree → stop.

## Step 7. (STANDARD — note one alternative)
"Bump the pool" changes nothing for single-request latency; might reduce queuing only under dozens of concurrent requests, but the dominant cost is still uncached FX. Mental model: pool starvation causes *queueing between requests*, not high *individual request latency*. Silent failure: endpoint stays slow, ticket closed without re-measuring.

## Step 8. Delta
Reflex: bump pool. Proposal: cache FX lookups by currency in rates.py; pool irrelevant. Deliberation changed diagnosis, file, and fix; the reflex was captured by Dana's authority framing; independent measurement produced a fully different answer. Shipping the reflex leaves the bug in production.

## FINAL RECOMMENDATION
Cause: `get_exchange_rate()` in `app/rates.py` called once per row (20×), each ~400ms simulated RTT, uncached; 20×0.4=8.0s ≈ 8.08s. Pool not involved: `max pool conns in use: 1`, acquired+released before any FX calls; starvation needs concurrent callers, so pool size is irrelevant at any value. **Dana's diagnosis is wrong.** Fix:
1. Cache get_exchange_rate by currency (only 3: EUR/GBP/JPY) — `@functools.lru_cache(maxsize=None)` or a request-scoped dict pre-fetched before the loop → 20 calls → ≤3 → ~8s to ~1.2s; warm → ~5ms.
2. Do not change db/pool.py (solves a different problem — concurrent throughput — only relevant if profiling under concurrency shows real contention).
3. After caching, re-run bench.py; verify FX calls drop 20→3 and elapsed ~1.2s.
Confidence high — two independent sources converge.
