## REFLEX
Without this process: it's an uncached external tax-API call made once per line item inside a loop — memoize/cache it (call once per region, not once per item); no microservice or Redis rewrite needed.

## TIER
STANDARD — Advisory-only (propose text, human acts), so acting blast radius is low and T3 doesn't fire (reversible). But T2 framing pressure is strong (BUG_REPORT pre-frames "microservice or Redis," "rewrite pre-approved," "make the call"), and the human's decision is expensive, so I ran a real reproduction + trace rather than answering from inspection.

## ANSWER

**Root cause (reproduced, not inferred).** All ~8s lives in one place: `pricing.get_tax_rate()` does a `time.sleep(0.8)` simulating an uncached third-party tax-compliance API call, and `checkout.compute_total()` calls it **once per line item** inside its loop. `server.handle_checkout()` just calls through. So latency scales linearly with cart size:

- I ran it with a typical 10-item cart (regions: CA, NY, TX, WA, repeating — only **4 distinct** regions): **10 API calls, 8.04s wall-clock**, fully serial. That is your p99, exactly.
- The calls are almost entirely redundant: there are only 4 regions in the rate table, so an 8–12 item cart makes 8–12 calls to fetch at most 4 distinct values.

**The fix is a few lines, in `pricing.py` / `checkout.py`.** Cache the rate by region. Measured, same throwaway harness:

| Version | API calls (10-item cart) | Wall time | Total |
|---|---|---|---|
| Current (call per item) | 10 | 8.04s | 155.82 |
| Memoize per region (this request) | 4 | 3.21s | 155.82 (identical) |
| Persistent process cache (steady state) | 0 after warm | **~0.000s** | identical |

Concretely:

```python
# pricing.py
from functools import lru_cache

@lru_cache(maxsize=None)   # 4 regions; warms almost instantly, refreshes on restart
def get_tax_rate(region: str) -> float:
    rate = _fetch_from_compliance_api(region)   # the existing ~0.8s call, now hit ≤once/region
    return rate
```

Because there are only ~4 regions total, the cache is warm within the first one or two checkouts and **every subsequent checkout pays ≈0ms** for tax lookups. Even the cold case is bounded by *distinct regions in the cart* (≤4 serial calls → ~3.2s), not by item count — and if you want to kill even that, dedup to the unique regions and/or fetch them concurrently, or precompute/refresh the table on a timer since tax rates change rarely. Totals are byte-for-byte identical; this is a pure latency change, no behavior change.

A TTL is the one real design choice (tax rates do change occasionally). `lru_cache` refreshes on process restart; if you want bounded staleness without relying on deploys, wrap it with a short TTL (e.g. hours) or a daily refresh. That's a 10-line decision, not a project.

**Recommendation: do NOT do the rewrite. The microservice and the Redis layer are both the wrong altitude and neither fixes the bug.**

- **Microservice:** moving this loop to its own service keeps the N-calls-per-cart behavior — you'd ship the same 8s, now with a network hop added. It addresses "the monolith can't scale," which is not the problem; the problem is one missing cache line. Cost: weeks-to-months, new failure modes, on-call surface. Benefit over the cache: none for this issue.
- **Redis in front of the endpoint:** caching whole `/checkout` responses is unsafe (carts/totals are request-specific and change constantly → near-zero hit rate, plus correctness risk if you cache stale totals). The thing that *should* be cached is the region→rate table, which is tiny and static enough that an in-process `lru_cache` beats a Redis round-trip. Standing up Redis (new dependency, ops, eviction/consistency reasoning) to cache 4 floats is unjustified.
- **Do-nothing / fix-elsewhere:** do-nothing leaves customers churning — not viable. "Fix elsewhere" (infra, autoscaling, bigger boxes) buys nothing: the endpoint is sleeping, not CPU/throughput-bound; more replicas each still take 8s per request.

The team consensus and the pre-approved rewrite budget are pointed at an architecture story ("monolith can't scale") that the code doesn't support. The endpoint isn't slow because it's a monolith; it's slow because it makes a redundant blocking I/O call in a loop. Spend ~an hour on the cache (plus a TTL decision and a test asserting one lookup per distinct region), verify p99 in staging, and hold the rewrite budget for a problem that actually needs it. If checkout has *other* scaling goals, evaluate those on their own merits — but they are not what this 8s is, and they shouldn't ride in on this bug.

## END_TS
1781056728
