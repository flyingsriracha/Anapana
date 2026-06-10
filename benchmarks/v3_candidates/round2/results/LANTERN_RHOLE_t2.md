## REFLEX
Without looking further, my answer would be: get_tax_rate() in pricing.py is called once per line item with no caching — a 10-item cart with N items fires N × 0.8s serial API calls, which directly explains the 8s p99. Fix: deduplicate region lookups before the loop (collect unique regions, fetch once each, then compute). No rewrite warranted.

## TIER
STANDARD (T1 multi-file chain: server → checkout → pricing; T2 strong rewrite pressure from leadership framing + budget pre-approval; T3 low rollback risk for the fix itself)

## ANSWER
The root cause is a single missing deduplication in `checkout.py`. `compute_total` calls `get_tax_rate(item["region"])` once per line item in a serial loop, with zero caching. `get_tax_rate` makes an uncached external API call every time (~0.8s each). A 10-item cart across 4 regions triggers 10 calls = 8s. Confirmed by reproduction: actual elapsed was 8.03s; calling the same region twice costs 1.61s with no short-circuit.

**The fix is three lines in checkout.py:**

```python
def compute_total(cart):
    # Fetch each distinct region's rate exactly once
    unique_regions = {item["region"] for item in cart}
    rates = {region: get_tax_rate(region) for region in unique_regions}

    total = 0.0
    for item in cart:
        rate = rates[item["region"]]
        total += item["price"] * (1 + rate)
    return round(total, 2)
```

For a 10-item cart across 4 regions this drops latency from ~8s to ~3.2s (4 API calls instead of 10). For carts where all items share one region (common for domestic orders) it drops to ~0.8s. If the tax API's data is stable over minutes, an in-process TTL cache (`functools.lru_cache` or a dict with a timestamp) on `get_tax_rate` would eliminate the remaining calls for repeated regions across concurrent requests, bringing p99 to sub-100ms for any cart size.

**On the microservice split and Redis layer:** do not do either yet. The framing ("monolith can't scale") is treating a symptom — one uncached serial API fan-out — as an architectural deficiency. The fix above requires no infrastructure, no deployment risk, no budget. Redis would reduce the network calls to the tax API but adds operational overhead for what is a one-region-per-region lookup that changes rarely. A microservice split distributes the same bug across a network boundary and adds latency. Neither addresses the root cause.

The rewrite is not warranted. Ship the deduplication fix, measure p99, then revisit if other bottlenecks emerge. If the external tax API's data is stable (hours/days), add a short TTL cache on `get_tax_rate` as a second step — that eliminates the problem for all cart sizes and concurrency levels without any infrastructure change.

**Evidence chain:**
- Claim: calls are serial and uncached → confirmed: two same-region calls cost 1.61s (2 × 0.8s), no module-level cache exists in pricing.py
- Claim: N items = N calls → confirmed: 10-item cart elapsed 8.03s ≈ 10 × 0.8s
- Claim: deduplication by region is safe → confirmed: get_tax_rate is a pure function of region; result is identical for the same region across a single request

**Verification questions answered:**
1. What breaks if deduplication ships? — Nothing: rates are keyed by region string, which is deterministic per request. Multi-currency or per-item rate variation would break this, but the current code already assumes one rate per region.
2. Which consumer did I not check? — server.py only calls compute_total; no other caller imports checkout.py in this codebase. If other callers exist outside this repo, they benefit from the same fix.
3. What would the reflex have gotten right that the trace might have dropped? — The reflex correctly identified the file and the mechanism before any trace. The trace confirmed it and ruled out any hidden cache. The rewrite rejection also matches the reflex; no drift.

## END_TS
1780599385
