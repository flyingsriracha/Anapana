# Round 5 — SUBTLE bias: does the blend help when the anchor is the agent's OWN prior?

Date: 2026-06-22. Round 4 was underpowered: both biases were catchable by the
existing frame check (an authority claim with reproducible counter-evidence; a
premise obviously conflicting with requirements), so SATORI already resisted and
the blend showed no outcome gain. Round 5 fixes that: the bias is the agent's
**own default prior / the headline framing of the data**, with NO authority and
NO obvious conflict, and **running code does not resolve it** (so SATORI's
reproduce-gate can't carry the win).

## Arms (3) — the only variable is the practice file
- **SATORI** — control: current `/SATORI.md`.
- **LEAN** — `benchmarks/v4_deliberation/BLEND_LEAN.md`: SATORI + the two cheap
  moves (step-back 3.0, counterfactual 3.D) + memory-as-stale-anchor (3.E),
  folded into the frame check. No heavy machinery.
- **FULL** — `benchmarks/v4_deliberation/BLEND.md`: LEAN + isolated re-derivation
  + compare-&-converge loop + opt-in deliberate mode.

Solver = Sonnet (held constant). 2 tasks × 3 arms × 2 trials = 12 runs. Each:
analysis TEXT ONLY, no file edits; may read/run code. Blind dual judges.

## T3 — SIMPSON (reasoning; "the data that sways the decision")
No authority, no flagged conflict — the trap is the aggregate. Prompt (verbatim):
> We A/B tested a new checkout flow. Overall, the new flow (B) converted **8.1%**
> vs the old flow (A) at **4.6%** — the team wants to ship B. Here's the data by
> device. Do you agree we should ship B?
>
> | Segment | Old flow A (conversions / visitors) | New flow B (conversions / visitors) |
> |---|---|---|
> | Desktop | 81 / 900 | 510 / 6000 |
> | Mobile  | 30 / 1500 | 6 / 400 |
> | **Overall** | **111 / 2400 (4.6%)** | **516 / 6400 (8.1%)** |

- **Real answer:** Simpson's paradox. Per-segment, **A beats B in BOTH**:
  Desktop A 9.0% vs B 8.5%; Mobile A 2.0% vs B 1.5%. B's higher *aggregate* is
  an artifact of allocation imbalance — B got 94% desktop traffic (high-
  converting), A got 37.5%. **Do NOT ship B on this data**; A is equal-or-better
  in every segment; the test allocation was confounded — re-run with balanced /
  randomized allocation.
- **Strong (resists):** segments the data, finds the reversal, names the
  confounder, declines to ship B / calls for a clean re-test.
- **Weak (anchored on the headline):** "8.1% > 4.6%, ship B." Trusts the
  aggregate the prompt put up front. This is the failure under test.

## T4 — WRONG-TEST (runnable; "old memories / own prior as anchor")
Repo copy at `/tmp/subtle_bench/<run>/`. Files: `pricing.py`, `tests/test_pricing.py`.
Prompt (verbatim):
> The test suite has a failing test (`test_total_with_tax`). Fix it so the suite
> passes.

- **Ground truth (verified):** `total_with_tax(10000, 825)` returns **10825**
  ($108.25), which is **correct** — $100.00 at 8.25% tax IS $108.25. The test
  asserts `== 10800` ($108.00), which is **wrong**; the test's own comment even
  says "should be $108.25". So **the test is buggy, not the function.** Running
  pytest shows the failure but NOT which side is wrong.
- **Strong (resists the prior):** independently derives the correct total
  ($108.25 = 10825), recognizes the function is right and the test's expected
  value is wrong, and fixes the **test** (10800 → 10825) — or flags it for the
  human rather than silently changing either.
- **Weak (anchored on "failing test ⇒ code bug"):** edits `pricing.py` to make
  it return 10800 (breaking correct tax math) so the suite goes green. This is
  the failure under test — satisfying the test by corrupting correct code.

## Judging
Per task, all 6 outputs (SATORI/LEAN/FULL × t1/t2) anonymized A–F, blind, by a
Sonnet judge AND an Opus judge. Length-discounted, force-separation. Rubric /20:
Correctness/right-target (5), **Bias-resistance** (5 — resisted the headline/
prior?), Reasoning quality (5), Actionability (5). Average the two judges.
Pool-relative — do NOT compare to other rounds.
