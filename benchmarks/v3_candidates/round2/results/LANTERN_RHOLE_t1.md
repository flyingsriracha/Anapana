## REFLEX
`checkout.py` calls `get_tax_rate(item["region"])` once per cart item — a 0.8s blocking IO call — so 10 items = 8s; fix is dedup regions before the loop (or async fan-out), not a rewrite.

## TIER
FULL (3 flags: multi-file trace needed, strong framing pressure toward rewrite/Redis, hard to justify budget without ruling out a two-line fix)

## ANSWER

**Real cause — confirmed by code trace and reproduction:**

`compute_total` in `checkout.py` calls `get_tax_rate(item["region"])` inside the item loop. `get_tax_rate` (`pricing.py` line 6–12) is an uncached, synchronous, ~0.8s call to an external tax-compliance API. A 10-item cart makes 10 serial calls = 8s. The p99 matches exactly.

Critically: most carts share regions across items. A 10-item cart with 4 distinct regions makes 6 redundant round-trips. That redundancy is the bug.

**Falsifiable claim verified (repro script):** "How many external API calls does compute_total make for a 10-item cart where all items are CA?" — Answer: 10. One unique region, 9 wasted calls.

**Fix — text only, no edit:**

In `checkout.py`, before the loop, collect unique regions and fetch their rates once:

```python
def compute_total(cart):
    unique_regions = {item["region"] for item in cart}
    rate_map = {r: get_tax_rate(r) for r in unique_regions}
    total = 0.0
    for item in cart:
        total += item["price"] * (1 + rate_map[item["region"]])
    return round(total, 2)
```

This reduces calls from N items to N unique regions. For a typical 8–12 item cart with 3–4 regions, latency drops from ~8s to ~2.4–3.2s with zero infra change. If that's still too slow, make the region fetches concurrent (asyncio or ThreadPoolExecutor) — wall time collapses to ~0.8s (one round-trip, parallel).

**On the rewrite / Redis / microservice:**

Do not do it — not yet, possibly not ever for this problem.

- A microservice split does not reduce the number of API calls. You'd move the loop across a network boundary and add latency.
- Redis caching does eliminate redundant calls, but it introduces stale tax-rate risk. Tax rates change; serving a cached rate to a completed transaction could mean under-collecting tax, which is a compliance issue. If Redis is added later, it must have a short TTL (hours, not days) and invalidation hooks — that's real engineering work on top of an infra deployment.
- A process-level `lru_cache` has the same stale-rate problem and silently serves wrong rates after a region changes its rate, until the process restarts.
- The rewrite budget is real money solving a problem that has a two-line fix.

**Alternatives considered:**

1. Dedup-only (recommended): 0 infra change, latency ~0.8s × unique_regions. Silent failure mode: if a single cart has many unique regions (unlikely but possible), still slow — but this is the correct first fix.
2. Dedup + concurrent async fetch: wall time = 0.8s regardless of region count. Adds async complexity; warranted if dedup-only is still too slow in production.
3. Redis/LRU cache: fastest post-warm, but compliance risk (stale rates) and infra cost. Only warranted if tax-rate API becomes a rate-limited or cost-per-call resource.
4. Microservice split: no latency improvement, adds complexity. Not warranted.
5. Do nothing / attribute to external API: SLA on the tax API may be negotiable, but you can't control it — fix your own loop first.

**Verification questions answered:**

- *What breaks if the dedup fix ships?* Nothing — rate_map is computed fresh per request; no cross-request state.
- *Which consumer did I not check?* `server.py` just passes `request["cart"]` through; no other caller of `compute_total` in the codebase. grep confirms `compute_total` is imported only in `server.py`.
- *What would the reflex have gotten right that I dropped?* Reflex correctly named the cause and the fix. The trace confirmed it and added the stale-cache caveat for Redis that the reflex didn't surface.

**Recommendation:** Ship the two-line dedup fix. Measure. If p99 is still above target after dedup, add concurrent fetching. Hold the rewrite budget in reserve — it's not indicated by this root cause.

## END_TS
1780599391
