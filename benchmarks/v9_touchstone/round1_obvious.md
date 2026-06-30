# TOUCHSTONE benchmark — scoring record (gitignored)

Date: 2026-06-30. Protocol: CRUCIBLE-style. One artifact (a pricing module with a
planted bug + a gamed/green test suite), 4 solver runs, blind dual-judge on a /25
rubric. All solvers = Claude Sonnet 4.6, so the only variable is the discipline.

## Setup
- Fixture: `fixture/pricing.py` (gold rate coded 15%, spec says 20% — live
  overcharge) + `fixture/test_pricing.py` (11 pass / 1 skip, ~100% line coverage,
  but theater: tautological gold tests, assertion-free tests, over-mocked bronze,
  and the one spec-correct test `@skip`-ped "flaky").
- Arms: **2 baseline** (just "review it, can we ship?") + **2 TOUCHSTONE** (told to
  load + follow a name-neutralized copy of the practice).
- Judges: 1 Opus + 1 Sonnet, each blind, four submissions anonymized W/X/Y/Z with
  brand/framing stripped. Rubric: 5 categories × 5 pts (real bug / integrity-skip
  gate / test-genuineness / resisted green=ship / verdict+depth).

## Hidden mapping
| Label | Arm | Run |
|---|---|---|
| W | baseline | base_1 |
| X | **TOUCHSTONE** | ts_2 |
| Y | baseline | base_2 |
| Z | **TOUCHSTONE** | ts_1 |

## Scores
| Submission | Arm | Opus judge | Sonnet judge | Avg |
|---|---|---|---|---|
| X | TOUCHSTONE | 25 | 25 | **25.0** |
| Z | TOUCHSTONE | 24 | 24 | **24.0** |
| W | baseline | 21 | 23 | **22.0** |
| Y | baseline | 19 | 21 | **20.0** |

- **TOUCHSTONE avg 24.5  vs  baseline avg 21.0  → +3.5 / 25 separation.**
- **Both judges, independently, ranked X > Z > W > Y** — identical ordering;
  TOUCHSTONE arms took 1st and 2nd on both cards. Unanimous.

## Where the gap lives — category by category
The baselines were NOT weak. On categories 1–4 they essentially tied the
TOUCHSTONE runs:
- Cat 1 (real bug): everyone found gold 15→20.
- Cat 2 (skip gate): everyone caught the `@skip`-ped spec test as concealment.
- Cat 3 (test-genuineness): everyone flagged the tautological / assertion-free /
  over-mocked tests.
- Cat 4 (resisted green): everyone refused "passes → ship."

The entire separation is **Category 5 (verdict + depth)**:
- Baselines: 2–3/5. Correct verdict, but findings *asserted in prose*. No run.
- TOUCHSTONE: 4–5/5. Findings *empirically proven*: an 8-mutant assay with a
  reported kill-rate (62.5–75%), surviving mutants named as the exact untested
  behaviors (**bronze rate, silver rate, floor-vs-ceiling**) the baselines walked
  past, a spec-derived golden-oracle table, and (ts_2) actually un-skipping the
  hidden test and confirming it FAILS 8500≠8000.
- The finding both judges singled out as decisive: the mutation that *corrects*
  gold to 20% is **KILLED** by the suite → the tests are "inverted sentinels"
  actively guarding the bug. Only the TOUCHSTONE runs surfaced this.

## Honest read
1. **No separation on the obvious traps.** A strong baseline model (Sonnet, no
   discipline) caught the planted bug, the skip, and the gamed tests on its own.
   The fixture's traps were catchable — the "floor at the ceiling" effect seen in
   the SATORI rounds. TOUCHSTONE did NOT catch something the baseline missed at the
   headline level.
2. **Real, unanimous separation on rigor/depth.** Where TOUCHSTONE pays off is
   forcing the agent past "these tests look bad" into measuring it (kill-rate) and
   finding the *additional* blind spots (bronze/silver exact rates, floor) plus
   empirically confirming the suppressed failure. That is exactly the step (§6
   mutation assay = "the empirical proof") the discipline exists to add, and both
   blind judges located the gap there independently.
3. **Caveats.** n=2 per arm (directional, not large-sample). Single solver model.
   Judges could see methodology cues (mutation tables, reflex header) that
   correlate with the arm — but the rubric rewards the *outcome* (proof/quantified
   detection), not the label, so this is the intended signal, not leakage; still,
   depth-advantage and visible-structure-advantage are entangled.

## Next: a discriminating fixture (proposed, not built)
This fixture proves TOUCHSTONE adds depth but cannot show it catching what a
baseline *misses*, because the traps were visible. A stronger v2 would plant a bug
that prose review CANNOT see but the assay CAN:
- NO `@skip`, NO tautological literal tells — every test looks reasonable.
- The bug lives only at a **boundary / floor edge** (e.g. rounding direction on a
  non-round input), so reading the tests doesn't reveal it; only a boundary case
  or a mutation that survives does.
- Then a separation on **Category 1** (baseline misses the bug; TOUCHSTONE's
  mutation/boundary step finds it) would be the real prize.
