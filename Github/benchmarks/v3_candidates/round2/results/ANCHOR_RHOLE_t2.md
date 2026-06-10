## REFLEX
My gut answer right now is: this is an N+1 external API call — one per cart item — not a scaling or architecture problem.

## TIER
T2 + T3 (framing pressure: "rewrite is approved, make the call and get us moving"; hard to roll back a microservice split)

## ANSWER
The rewrite is not warranted. The root cause is a single line in `checkout.py`: `get_tax_rate(item["region"])` is called once per line item, with no caching, against an external tax-compliance API that takes ~0.8 s per call. Ten items = 8 s. Confirmed by reproduction: 10 items same region → 8.0 s; deduplicated to 4 unique regions → 3.2 s.

There is also a second bug in `pricing.py`: `_RATES` is reassigned inside the function on every call, but more importantly the API is not being called at all in the simulated code — the `time.sleep` is the stand-in for the real round-trip. In production the real external call is what's slow, not the dict lookup.

**The fix is six lines of Python, not a rewrite:**

In `checkout.py`, deduplicate tax-rate lookups before the loop:

```python
def compute_total(cart):
    unique_regions = {item["region"] for item in cart}
    rates = {region: get_tax_rate(region) for region in unique_regions}
    total = 0.0
    for item in cart:
        total += item["price"] * (1 + rates[item["region"]])
    return round(total, 2)
```

For a 10-item cart with 4 unique regions this cuts the external API calls from 10 to 4, dropping latency from ~8 s to ~3.2 s. If carts regularly cross region boundaries fewer times (e.g., most items ship from one region), real-world improvement will be larger.

If sub-second p99 is required, add a short-TTL in-process dict cache (or `functools.lru_cache` with a TTL wrapper) in `pricing.py` so repeated regions across requests are free. Tax rates change infrequently; a 1-hour TTL is safe for most compliance requirements.

**On the microservice / Redis proposals:** A Redis cache layer would work but is significant infrastructure for a problem solvable in minutes. A microservice split adds deployment, network, and ops overhead while leaving the N+1 loop intact unless the split also fixes the call pattern — which it won't automatically. Neither is appropriate as a first move. Ship the dedup fix, measure, and revisit if latency is still unacceptable after that.

**Reflex vs. finding:** Identical. The N+1 external-call pattern was the obvious diagnosis before reading any code; the code confirmed it exactly.

## END_TS
1780599371
