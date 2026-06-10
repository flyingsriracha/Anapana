## REFLEX
Caching or dedup the tax lookup — probably N+1 calls to a slow external API.

## TIER
FULL (3/3 triggers: multi-file cross-system, strong rewrite/microservice pressure + "make the call", expensive rollback of a rewrite)

## ANSWER
The p99 is 8s because `compute_total` calls `get_tax_rate(region)` once **per line item** — 10 items → 10 serial round-trips to the external tax-compliance API at ~0.8s each. A 10-item cart with 3 distinct regions takes 8s; the minimum fix uses 3 calls. Confirmed by running the code: 10-item cart, real sleep, 8.03s. With region dedup it runs in 2.41s.

**Root cause (one line): N redundant serial external-API calls — one per cart item instead of one per unique region.**

**The fix (text only, no edits):** In `checkout.py` `compute_total`, deduplicate regions before calling `get_tax_rate`, then reuse cached rates in the item loop:

```python
def compute_total(cart):
    unique_regions = {item["region"] for item in cart}
    rates = {r: get_tax_rate(r) for r in unique_regions}  # N_regions calls, not N_items
    total = sum(item["price"] * (1 + rates[item["region"]]) for item in cart)
    return round(total, 2)
```

For a typical 8–12 item cart with 2–4 distinct regions, this brings latency from 6–10s to 1.6–3.2s on the external API alone. If that's still too slow, parallelize the region lookups with `concurrent.futures.ThreadPoolExecutor` (3 concurrent calls → ~0.8s total for any cart).

**On the rewrite / microservice / Redis question:** Do not do it. The problem is not the monolith, not cache infrastructure, not architecture — it is a loop that issues redundant network calls. A microservice split moves the same bug to a different process. A Redis layer in front of `/checkout` would cache the *full cart total* (wrong: cart contents vary per user) or add complexity for no gain. The correct cache target, if needed after the dedup fix, is the tax-rate lookup itself (`@functools.lru_cache` on `get_tax_rate` or a short-TTL in-process dict), which is a 5-line change. Spend the rewrite budget after you confirm the fix is insufficient — current evidence doesn't support that.

**Inversion check (what would make it worse):** Adding Redis in front of the endpoint without fixing the loop — you'd still issue 10 API calls inside the cache miss path, and cache hits would be wrong for different carts. Microservice split makes the N+1 problem a distributed N+1 problem with added network overhead.

**Reflex vs. proposal:** Reflex ("N+1, dedup the lookup") was correct. What the process added: explicit verification that the rewrite pressure is a framing trap (the team diagnosed "monolith can't scale" from a symptom that has nothing to do with monolith scale), and the inversion check ruling out Redis as a fix.

## END_TS
1780599389
