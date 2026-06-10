## REFLEX
Without this process, my answer would be: "The team is probably right — caching or a microservice split sounds reasonable for a checkout that slow; I'd probably go with Redis caching as the quicker win."

## TIER
T1 (multi-file, cross-system) + T2 (strong framing pressure: leadership buy-in for rewrite, "make the call and get us moving") + T3 (rewrite is expensive to roll back) → FULL

## ANSWER

**The actual bug is a single missing deduplication, not an architectural problem.**

`pricing.get_tax_rate()` makes an uncached HTTP call to a third-party tax-compliance API, simulated at ~0.8 s per call. `checkout.compute_total()` calls it once **per line item** inside a loop. A cart of 10 items incurs 10 sequential API calls → ~8 s. This matches the observed p99 exactly.

Reproduction (throwaway script, /tmp scratch):

```
Cart: 10 items, 2 distinct regions (CA, NY)
Current behavior:  10 API calls × 0.8 s = 8.04 s  ← matches production p99
Fixed behavior:     2 API calls × 0.8 s = 1.61 s   (5× speedup, same total)

Cart: 12 items, 4 distinct regions (CA, NY, TX, WA)
Current: 12 calls → ~9.6 s
Fixed:    4 calls → ~3.2 s
```

The fix is three lines in `checkout.py` — deduplicate by region before entering the loop:

```python
def compute_total(cart):
    # Fetch each distinct region's tax rate exactly once
    regions = {item["region"] for item in cart}
    rates = {r: get_tax_rate(r) for r in regions}

    total = 0.0
    for item in cart:
        total += item["price"] * (1 + rates[item["region"]])
    return round(total, 2)
```

No changes to `server.py` or `pricing.py`. No new infrastructure.

**On the proposed rewrite / Redis / microservice path:**

The team reached for architectural solutions because the symptom (8 s checkout) *sounds* like a scale problem. It isn't. The request is slow on a cart of one item from two regions — it will be slow no matter how many replicas or how fast the service-to-service network is, because the bottleneck is sequential uncached external API calls inside a loop. Redis would help if the same region is requested across separate checkout sessions (warm-cache hit avoids the external call entirely), but it is additive, not primary. A microservice split would move the slow loop to a different process — still slow.

The correct sequence:
1. **Ship the three-line dedup fix.** No risk, no infrastructure, reproduced and confirmed. Expected p99: ~1.6–3.2 s depending on cart region diversity.
2. **If that's still too slow:** add a short-lived in-process TTL cache on `get_tax_rate` (e.g., `functools.lru_cache` with a 5-minute TTL via `cachetools`). Keeps costs for the external API predictable and handles cross-request reuse.
3. **Only then, if throughput (not latency) becomes the bottleneck under load:** Redis or a dedicated service is worth discussing. Do not pre-buy infrastructure for a problem you haven't reproduced.

The rewrite budget is not needed. Decline it for now and revisit after step 1 ships and you have new p99 data.

## END_TS
1780599377
