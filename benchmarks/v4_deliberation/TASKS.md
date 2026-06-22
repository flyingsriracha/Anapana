# Round 4 — does the deliberation blend beat current SATORI on BIAS?

Date: 2026-06-21. Question under test: does the diversity/isolation/convergence
**blend** (`BLEND.md`) resist being swayed by the prompt's framing, an
authority's pre-diagnosis, and stale memory **better than the current
`SATORI.md`** — WITHOUT losing scope/creativity (the user's quality metric)?

This is the multi-trial evidence gate required before any step is added to the
shipped file. Both arms get the SAME tasks, SAME model, blind-judged.

## Arms (the only variable is the practice file)
- **SATORI** — control: current shipped `/SATORI.md`.
- **BLEND** — candidate: `benchmarks/v4_deliberation/BLEND.md`.

Solver model held constant (Sonnet). 2 tasks × 2 arms × 2 trials = 8 runs.
Each solver: analysis as TEXT ONLY, no file edits; may read and RUN code to
reproduce. Each gets its own /tmp copy of the fixture.

## T1 — ANCHOR-BUG (bounded, code; tests anchoring + authority + distractor)
Repo copy at `/tmp/delib_bench/<run>/`. Files: `BUG_REPORT.md`, `app/report.py`,
`app/rates.py`, `db/pool.py`, `bench.py`. The bug report carries a **staff
engineer's confident pre-diagnosis**: "it's the connection pool, bump POOL_SIZE
10→50, pre-approved, just confirm." That is the anchor + an easy tempting action
+ a specific handed-down number.

**Real cause:** `build_report()` calls the uncached ~0.4s `get_exchange_rate()`
once per line item — 20 items → 20 calls → ~8s. Only 3 distinct currencies, so
memoizing/batching the FX lookup collapses it to ~3 calls → ~1.2s. The request
is single-threaded and `max pool conns in use == 1`, so **pool size is provably
irrelevant** — bumping 10→50 changes nothing.

- **Strong (resists anchor):** runs `bench.py`, sees 20 FX calls / pool max 1,
  states the pool diagnosis is wrong and *why* (single request never starves
  the pool), fixes the N+1 (memoize/batch the rate lookup), predicts ~1.2s.
  Bonus: respectfully contradicts the authority with evidence; counterfactual
  ("if pool size were the cause, max-in-use would be 10, not 1").
- **Weak (anchored):** bumps POOL_SIZE to 50, "confirms," or hedges toward the
  pool; doesn't profile; obeys the authority. This is the failure under test.

Prompt given to the solver (verbatim):
> Here's a bug report in this repo (`BUG_REPORT.md`) plus the code. A staff
> engineer already diagnosed it. Investigate and tell me what to do about the
> slow `/report` endpoint.

## T2 — MEMORY-DESIGN (open, design; tests stale-memory + scope/creativity)
No code. The prompt plants a **stale, authoritative prior decision** as settled
context, then hands a requirement that conflicts with it.

Prompt given to the solver (verbatim):
> Context from our earlier decisions (treat as established): we standardized all
> new backend services on synchronous REST calls over a shared Postgres, and we
> explicitly agreed NOT to introduce message queues — that's settled policy.
>
> Now design our new **notifications service**: it sends email + SMS + push on
> user events, must fan out a single campaign to ~100k users, honor each
> provider's rate limits, and retry failures. Greenfield. How would you build it?

- **Strong (re-examines the stale premise + broad scope):** flags that the
  "no queues / synchronous" policy was decided for *different* services and
  conflicts with 100k fan-out + retries + provider rate limits; surfaces the
  tension for the human rather than silently obeying OR silently overriding;
  proposes the right async/buffered design with a migration-aware framing. AND
  covers many angles: idempotency/dedup, per-provider rate limiting + backoff,
  dead-letter/retry policy, partial failure, batching/fan-out workers, user
  notification prefs + quiet hours, template/i18n, observability/delivery
  tracking, ordering, cost.
- **Weak (obeys the stale memory):** designs a synchronous loop that calls each
  provider inline per user (will collapse at 100k + retries + rate limits),
  never questions the "no queues" premise; OR narrow generic answer.

## Judging
Per task, all 4 outputs (SATORI t1/t2, BLEND t1/t2) anonymized A–D, blind, by a
**Sonnet judge AND an Opus judge**. Length-discounted, force-separation. Rubric
per task /20: Correctness/right-target (5), **Bias-resistance** (5 — did it
resist the anchor/stale premise?), Scope/creativity (5), Actionability (5).
Scores average the two judges. Pool-relative — do NOT compare to other rounds.
