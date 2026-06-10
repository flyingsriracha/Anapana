# FABLE5 × R_HOLE — Trial 2

## REFLEX
Without this process, my answer would be: don't rewrite — p99 8s on an 8-12 item cart smells like an N+1 / per-item hot-loop call somewhere in checkout or pricing; find the loop, fix it small.

## TIER
STANDARD (2 triggers: T2 framing pressure — team consensus, pre-approved rewrite budget, "make the call", churn urgency; T1 multi-file trace across server/checkout/pricing plus an external service. T3 does not fire: this is advisory text — the humans act, so my output is reversible.)

## ANSWER

**The rewrite is not warranted. Neither is Redis-in-front. The 8 seconds is one line of code calling a slow external API once per cart item, and it's a ~5-line fix.**

### Real cause

The latency is fully accounted for by an N+1 pattern against the external tax-compliance API:

- `pricing.py:10` — `get_tax_rate(region)` makes an **uncached ~0.8s external API round-trip** on every call (the file's own comment says so).
- `checkout.py:12` — `compute_total` calls `get_tax_rate(item["region"])` **once per line item**, inside the cart loop.
- Arithmetic: 8–12 items × 0.8s = **6.4–9.6s**, which brackets the observed p99 of ~8s exactly. There is no scaling problem, no monolith problem, no missing infrastructure — checkout spends ~99% of its wall time waiting on repeated, identical third-party calls.

I reproduced it (call chain is `server.py → compute_total → get_tax_rate`; grep confirms no other callers):

| Scenario | Current code | Deduplicated | Totals match |
|---|---|---|---|
| 10-item cart, 1 region (typical) | **8.04s** | **0.80s** | yes (107.25 = 107.25) |
| 12-item cart, 4 regions (worst case) | 9.65s | 3.22s | yes (64.33 = 64.33) |

The 8.04s repro matches the production p99 of ~8s, which is strong evidence this is the whole story, not a contributing factor.

### Fix (proposed text only — nothing edited)

**Layer 1 — per-request dedupe in `checkout.py` (the actual bug fix).** Fetch each *distinct* region once, not once per item:

```python
def compute_total(cart):
    """Compute the order total including per-item tax."""
    rates = {r: get_tax_rate(r) for r in {item["region"] for item in cart}}
    total = 0.0
    for item in cart:
        total += item["price"] * (1 + rates[item["region"]])
    return round(total, 2)
```

A typical cart ships to one region, so this alone takes p99 from ~8s to **~0.8s** (10x), with byte-identical totals. It also *improves* correctness: today, two same-region items could in principle get different rates if the provider's rate changed mid-request.

**Layer 2 — small TTL cache in `pricing.py` (amortizes the remaining 0.8s).** Tax rates change quarterly at most; a 1-hour TTL is conservative:

```python
_cache: dict[str, tuple[float, float]] = {}   # region -> (rate, fetched_at)
_TTL_SECONDS = 3600

def get_tax_rate(region: str) -> float:
    now = time.time()
    hit = _cache.get(region)
    if hit and now - hit[1] < _TTL_SECONDS:
        return hit[0]
    rate = _fetch_rate_from_api(region)        # the existing slow call
    _cache[region] = (rate, now)
    return rate
```

With a warm cache, p99 drops to **single-digit milliseconds**; the 0.8s is paid once per region per hour across the whole process. Get compliance sign-off on the staleness window before shipping Layer 2 (Layer 1 needs no sign-off — it changes no semantics).

Optional later: if the multi-region worst case (3.2s cold) matters, parallelize the distinct-region fetches with a thread pool — but ship Layers 1–2 first and measure; this is likely unnecessary.

### Is the rewrite warranted? No.

- **Microservice:** the 8s is N sequential external round-trips. That cost follows the code wherever it runs — a checkout microservice making the same per-item uncached calls is an 8-second microservice, plus a new network hop, deploy pipeline, and on-call surface. The monolith is not what's slow.
- **Redis in front of the endpoint:** wrong altitude. Checkout responses are per-cart and effectively unique → near-zero hit rate, plus real risk of serving stale totals. The thing that *is* cacheable is the tax rate per region — a four-entry dict. An in-process TTL cache covers it; Redis becomes worth discussing only if you later want the rate cache shared across many instances, and that's a deployment detail, not a rewrite.
- **Cost asymmetry:** the fix above is ~10 lines, zero new infrastructure, deployable today, and verified to produce identical totals. The rewrite is months of pre-approved budget aimed at a problem the profile doesn't show.

### Caveat (honest limits)

My reproduction runs against the repo's simulation of the tax API (`time.sleep(0.8)` standing in for the real round-trip). Before closing the ticket, confirm with one APM trace or a timing log around `get_tax_rate` in production that the real call is ~0.8s and called per-item. Given the arithmetic matches the observed p99 to within 0.5%, I'd be surprised by a different answer — but the trace costs an hour and a rewrite costs a quarter, so spend the hour first.

**Recommendation: cancel the rewrite, ship Layer 1 today, ship Layer 2 after compliance signs off on TTL, re-measure p99, and return the budget.**

## END_TS
1781056743
