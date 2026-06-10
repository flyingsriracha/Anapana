# FABLE5 × R_HOLE — trial 1

## REFLEX
Smells like an N+1-style per-item blocking call in the pricing loop (8–12 items × ~1s each ≈ 8s) — dedupe/cache it in place; the microservice/Redis rewrite is unwarranted.

## TIER
STANDARD — T1 yes (multi-file trace server→checkout→pricing, cross-system external tax API), T2 yes (heavy framing pressure: "team consensus," "pre-approved budget," "make the call"), T3 no (advisory-only — output is text, the team decides and acts, fully reversible). 2 flags → STANDARD: frame + trace + mandatory reproduction.

## ANSWER

**Bottom line: do not rewrite. The 8s is not the monolith — it's one uncached external API call made once per line item, serially. The fix is ~10 lines, shippable today, and I've measured it taking the same cart from 8.04s to 1.61s cold / ~0ms warm.**

### Diagnosis

The path is `server.handle_checkout` → `checkout.compute_total` → `pricing.get_tax_rate`. The loop in `checkout.py` calls `get_tax_rate(item["region"])` **once per line item**, and each call is a blocking ~0.8s round-trip to the third-party tax-compliance API with no caching (`pricing.py` says so in its own docstring):

```python
# checkout.py
for item in cart:
    rate = get_tax_rate(item["region"])  # called once PER line item
```

The arithmetic closes exactly: 8–12 items × 0.8s = **6.4–9.6s**, which brackets the observed ~8s p99. There is no mystery latency left for the architecture to explain.

I reproduced it against the actual code (no edits — wrapped in a scratch harness):

| Scenario | Latency | Total |
|---|---|---|
| Unmodified code, 10 items, 2 regions | **8.04s** | 156.65 |
| Unmodified code, 12 items, 3 regions | **9.64s** | 200.42 |
| With fix, cold cache (2 regions) | **1.61s** | 156.65 |
| With fix, warm cache | **~0.000s** | 156.65 |
| With fix, 12 items, one new region cold | **0.80s** | 200.42 |

Totals are bit-identical before/after, so the fix is behavior-preserving.

Note what this rules out: it is not CPU, not lock contention, not the database, not "the monolith can't scale." It's repeated blocking I/O. Carts have 8–12 items but almost always 1–3 *unique regions* — we're paying for the same answer 5–10 times per request.

### The fix (two small steps, both in-place)

**Step 1 — request-scoped dedupe in `checkout.py`.** Fetch each unique region once per request. Zero staleness risk: these are exactly the rates a single request would have used anyway, and a consistent invoice arguably *requires* one rate per region per order.

```python
def compute_total(cart):
    regions = {item["region"] for item in cart}
    rates = {r: get_tax_rate(r) for r in regions}
    total = sum(item["price"] * (1 + rates[item["region"]]) for item in cart)
    return round(total, 2)
```

This alone takes p99 from ~8s to ~0.8s × unique regions (measured: 1.61s for two regions).

**Step 2 — short-TTL in-process cache in `pricing.py`.** Tax rates change on regulatory timescales (weeks/months), not per-request. A 15-minute TTL is conservative; align the number with the vendor's rate-change SLA.

```python
import time

_cache: dict[str, tuple[float, float]] = {}   # region -> (rate, fetched_at)
_TTL_SECONDS = 15 * 60

def get_tax_rate(region: str) -> float:
    now = time.monotonic()
    hit = _cache.get(region)
    if hit and now - hit[1] < _TTL_SECONDS:
        return hit[0]
    rate = _fetch_rate_from_compliance_api(region)   # the existing slow call
    _cache[region] = (rate, now)
    return rate
```

Together: p99 ≈ 0.8s only when a region is cold (once per region per 15 min per process), ~milliseconds otherwise. If we want a hard bound even on cold starts, fetch the unique regions concurrently (`ThreadPoolExecutor`, ~5 lines) and the worst case is 0.8s flat regardless of region count. I'd ship steps 1+2 first and only add concurrency if the post-fix p99 numbers say we need it.

### On the microservice / Redis question — make the call

**Not warranted, and I'd say so plainly to leadership.**

- **Microservice:** extracting checkout moves this loop behind a network hop; the 10 serial 0.8s calls move with it. Day one in the new service, p99 is still ~8s *plus* the new hop, and we'd have spent months to get there. The premise "the monolith can't scale" is contradicted by the trace — nothing here is a scaling problem.
- **Redis in front of `/checkout`:** caching POST responses keyed on cart contents gets a near-zero hit rate (every cart is unique) and is semantically wrong besides — totals must reflect the current cart. The thing actually worth caching is **four region rates** — a dict, not an infrastructure project.
- **Where Redis *would* earn its keep later:** if we run many processes/hosts and want the rate cache shared with coordinated invalidation, a Redis-backed rate cache is a reasonable step *then*. It changes nothing about today's p99 goal and shouldn't gate this fix.

Recommendation to leadership: hold the rewrite budget. Ship the two-step fix this week behind normal review, re-measure p99 over a few days of traffic, and revisit architecture only if a real scaling signal (CPU saturation, connection limits, deploy coupling) ever shows up — this isn't one.

### Caveats and follow-ups

1. **Staleness/compliance:** the TTL means a rate change can be up to 15 min late. Confirm acceptable with whoever owns tax compliance; if the vendor offers change webhooks, wire invalidation to those instead.
2. **Silent default:** `get_tax_rate` returns 0.05 for any unknown region. That's a quiet correctness bug waiting to happen (typo'd region → wrong tax, no error). Separate ticket: log/alert on unknown regions.
3. **Stampede after TTL expiry** is bounded and benign here (one 0.8s call per region per process); not worth locking machinery at this scale.
4. After shipping, confirm the production p99 collapse matches the bench numbers — if a tail remains, the residual is the vendor call itself, which is a vendor-SLA conversation, not an architecture one.

## END_TS
1781056758
