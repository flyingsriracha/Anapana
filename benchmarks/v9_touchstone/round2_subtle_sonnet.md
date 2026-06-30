# TOUCHSTONE benchmark v2 — scoring record (gitignored)

Date: 2026-06-30. Same protocol as v1 (CRUCIBLE-style, blind dual-judge /25), but a
DISCRIMINATING fixture: the planted bug is meant to be invisible to prose review.

## Setup
- Fixture: `fixture_v2/commission.py` — `round(sale_cents * 2.5 / 100)`. Python's
  `round()` is BANKER'S rounding (half-to-even); spec says **halves round UP**. They
  diverge only at even-integer + 0.5 cent results → sale ∈ {20,100,180,260,...}.
  sale=100 → code 2¢, spec 3¢. Real money bug behind green.
- Test suite (`test_commission.py`): 9 tests, all honest/exact/passing, **no gaming
  tell** (no skip, mock, tautology, or assertion-free test). Two tests *look* like
  rounding coverage (1.25→1, 1.75→2) but sit where banker's and half-up agree. The
  even-half boundary is never tested.
- Arms: 2 baseline + 2 TOUCHSTONE, all Sonnet 4.6. Judges: Opus + Sonnet, blind,
  submissions anonymized P/Q/R/S, brand stripped.

## Hidden mapping
| Label | Arm | Run |
|---|---|---|
| P | baseline | base_v2_1 |
| Q | **TOUCHSTONE** | ts_v2_2 |
| R | baseline | base_v2_2 |
| S | **TOUCHSTONE** | ts_v2_1 |

## Scores
| Submission | Arm | Opus | Sonnet | Avg |
|---|---|---|---|---|
| Q | TOUCHSTONE | 25 | 25 | **25.0** |
| S | TOUCHSTONE | 23 | 24 | **23.5** |
| P | baseline | 20 | 21 | **20.5** |
| R | baseline | 20 | 21 | **20.5** |

- **TOUCHSTONE avg 24.25 vs baseline avg 20.5 → +3.75 / 25.**
- **Both judges independently ranked Q > S > {P,R}** — TOUCHSTONE arms 1st & 2nd on
  both cards. Unanimous, same as v1.

## The result I did NOT expect — Category 1 did not separate
The whole point of v2 was to make the bug invisible to reading so a baseline would
SHIP it and TOUCHSTONE would catch it (a Category-1 separation). That did not happen:
**all four runs caught the bug.** Both baselines found it by *inspection* — Sonnet
knows Python's `round()` is banker's rounding, built the exact half-cent failure
table, and flagged the vacuous rounding tests, with no discipline at all.

Worse for the hypothesis: **both TOUCHSTONE runs admitted they suspected the
divergence before the assay** ("I suspected that divergence before reading a single
test"; reflex 4/10 and 6/10). So even in the TOUCHSTONE arm the mutation step
*proved* the bug, it didn't *discover* it. At Sonnet strength, knowledge — not
scaffolding — is what found the bug, in every arm.

## Where the +3.75 actually comes from — Category 5 only
Identical to v1: cat 1–4 cluster high across all four (everyone found the bug,
boundary-tabled it, diagnosed the gap, refused green). The entire gap is **Category
5 (verdict + depth)**:
- Baselines: 2/5. Correct, articulate, but *asserted* — no mutation, no kill-rate,
  vaguer remediation, one unverified claim (`commission_cents(-100) == -2`).
- TOUCHSTONE: 4–5/5. *Proved* it — ran an 8-mutant campaign, reported kill-rate
  (75%), and the decisive move both judges singled out: mutated the code to the
  spec-correct `ROUND_HALF_UP` and watched all 9 tests **stay green** → the suite's
  blindness becomes a demonstrated measurement, not an argument. Concrete fix
  (`Decimal`/`ROUND_HALF_UP` + boundary test).

## Cross-round conclusion (v1 + v2)
Two fixtures — one obvious bug (v1), one subtle (v2) — same outcome both times:

1. **A strong solver model (Sonnet) catches the bug regardless of discipline.** The
   "find the bug" floor is at the ceiling for a single-function artifact, whether
   the bug is a glaring `gold:15` or a `round()` half-to-even subtlety. We could not
   manufacture a Category-1 separation by making the bug subtler — Sonnet just knew.
2. **TOUCHSTONE reliably adds ~3.5–4 pts of empirical depth (Category 5).** Both
   blind judges, both rounds, rank the two TOUCHSTONE runs 1st and 2nd. The discipline
   converts "I can see this is wrong" into "I mutated it to the spec and proved the
   suite is blind" — quantified, reproducible, with concrete fixes.

So the honest, demonstrated value of TOUCHSTONE at this scale is **rigor and proof,
not bug-discovery a strong model would otherwise miss.**

## To actually show "catches what baseline misses" — drop the floor
The benchmark can't show a discovery gap while the solver is strong enough to know
every gotcha. Two ways to lower the floor so the scaffolding has to do the work:
- **Weaker solver model.** Re-run THIS v2 fixture with Haiku 4.5 on both arms.
  Hypothesis: baseline-Haiku does NOT reliably know the `round()` banker's gotcha and
  ships the bug; TOUCHSTONE-Haiku's mechanical mutation step (round→floor/ceil all
  survive → "rounding untested") forces it to the boundary and catches it. That would
  be a real Category-1 separation — the discipline substituting for knowledge the
  model lacks. **This is the most informative next run.**
- **Larger / multi-file artifact** where no single function can be fully reasoned
  about, so the bug can't be caught by inspection even by a strong model.
