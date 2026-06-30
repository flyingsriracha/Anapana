# TOUCHSTONE benchmark — Haiku round (gitignored)

Date: 2026-06-30. Same v2 fixture (commission / banker's-rounding bug), same blind
dual-judge /25, but **solver model = Haiku 4.5** on all 4 arms — to drop the floor
and test whether the discipline catches a bug a weaker model would otherwise miss.

## Hidden mapping
| Label | Arm | Run |
|---|---|---|
| A | baseline | base_v2h_1 |
| B | **TOUCHSTONE** | ts_v2h_2 |
| C | baseline | base_v2h_2 |
| D | **TOUCHSTONE** | ts_v2h_1 |

## Scores
| Submission | Arm | Opus | Sonnet | Avg |
|---|---|---|---|---|
| B | TOUCHSTONE | 25 | 25 | **25.0** |
| D | TOUCHSTONE | 24 | 24 | **24.0** |
| A | baseline | 19 | 20 | **19.5** |
| C | baseline | 17 | 18 | **17.5** |

- **TOUCHSTONE avg 24.5 vs baseline avg 18.5 → +6.0 / 25.**
- **Both judges ranked B > D > A > C** — TOUCHSTONE 1st & 2nd, unanimous (6/6 cards
  across all three rounds now).

## Key results
1. **Dropping to Haiku did NOT produce a Category-1 (discovery) separation.** All 4
   Haiku runs — both baselines included — caught the banker's-rounding bug, named the
   exact failing inputs (20→1, 100→3), and reached do-not-ship. Banker's rounding is
   a *famous* Python gotcha; even Haiku knows it. So the bug-discovery floor stayed at
   the ceiling at Haiku strength too.
2. **The depth gap WIDENED as the model weakened.** v1 Sonnet +3.5, v2 Sonnet +3.75,
   **v2 Haiku +6.0.** Reason: TOUCHSTONE's score is remarkably *model-stable* (~24.25–
   24.5 in every round, both models), while the baseline's score *drops* with model
   strength (21.0 → 20.5 → 18.5). A weak model left alone finds the bug but only
   *asserts* it (no mutation, no kill-rate, one factual slip in C's boundary table);
   the same weak model under the discipline still runs the full assay and *proves* it
   (mutation kill-rate + the decisive "swap in ROUND_HALF_UP, watch all 9 tests still
   pass" demonstration). **The discipline lifts a weaker model's rigor MORE.**

## Confound to disclose
The working dir is `/tmp/touchstone_bench/…`, so the string "touchstone" is visible
in every agent's path — and baseline A literally referenced "TOUCHSTONE's rigor" in
its output. It did NOT cause the catch (A found the bug by reasoning), but the brand
leaked. Future rounds should use a neutral dir name (e.g. `/tmp/rigor_bench/`).

## Three-round synthesis (the bottom line)
| Round | Solver | Bug | TOUCHSTONE | Baseline | Gap | TS rank |
|---|---|---|---|---|---|---|
| v1 | Sonnet | obvious (gamed suite) | 24.5 | 21.0 | +3.5 | 1st & 2nd |
| v2 | Sonnet | subtle (banker's round) | 24.25 | 20.5 | +3.75 | 1st & 2nd |
| v2 | Haiku | subtle (banker's round) | 24.5 | 18.5 | +6.0 | 1st & 2nd |

**What TOUCHSTONE demonstrably does:** produce consistent, model-stable test-audit
rigor (~24.5/25 whether Sonnet or Haiku) — empirical proof via mutation, quantified
kill-rate, and the spec-swap demonstration of suite blindness — and it raises a
*weaker* model's rigor the most (acts as a floor-raiser/equalizer).

**What it was NOT shown to do:** help a model FIND a bug it would otherwise miss. In
3 rounds I could not manufacture a discovery gap, because every planted bug was
catchable by reasoning (obvious gaming, or the famous banker's-rounding gotcha).

## The still-untested claim → the one experiment left
"Substitutes for knowledge the model lacks" remains *plausible but unproven*: even
Haiku knew banker's rounding. To actually test discovery, plant a **non-famous,
domain-specific boundary bug that requires COMPUTING, not recalling** — e.g. an
off-by-one in a tax-bracket / tiered-rate threshold, or an inclusive-vs-exclusive
bound in a custom business rule with no well-known name. Hypothesis: baseline-Haiku
(and maybe baseline-Sonnet) ships it; the discipline's mechanical mutation/boundary
step forces it out. That is the experiment that would finally show a Category-1 gap —
or honestly fail to, and bound the claim.
