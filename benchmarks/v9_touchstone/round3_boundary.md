# TOUCHSTONE benchmark v3 — the discovery test (gitignored)

Date: 2026-06-30. Purpose: finally test the DISCOVERY claim — plant a NON-famous
domain bug (no language gotcha, no spec/code constant mismatch) that requires
*computing* a boundary, not *recalling* a trap, and see if a baseline ships it while
the discipline catches it. Run at BOTH model strengths. Neutral dir `/tmp/rigor_bench/`
+ neutral `checklist.md` (fixes the v2-Haiku path-leak confound).

## Fixture
`pricing_tiers.py`: `tier = quantity // 10` (should be `(quantity-1)//10`). Spec tiers
1-10/11-20/21+. Bug fires ONLY at the exact boundaries: q=10 → code 4500 vs spec
5000; q=20 → 8000 vs 9000. Every other quantity correct. 9-test green suite tests
q=9 and q=11 (straddling) and q=21 — looks boundary-tested, never tests q=10/q=20.

## Arms (8): 2 baseline + 2 TOUCHSTONE at EACH of Haiku 4.5 and Sonnet 4.6.

## Hidden mapping
| Label | Arm | Run | | Label | Arm | Run |
|---|---|---|---|---|---|---|
| S1 | base Haiku | base_h_1 | | S5 | base Sonnet | base_s_1 |
| S2 | **TS Sonnet** | ts_s_1 | | S6 | **TS Sonnet** | ts_s_2 |
| S3 | base Sonnet | base_s_2 | | S7 | base Haiku | base_h_2 |
| S4 | **TS Haiku** | ts_h_2 | | S8 | **TS Haiku** | ts_h_1 |

## Scores (Opus judge / Sonnet judge / avg)
| Sub | Arm | Opus | Sonnet | Avg |
|---|---|---|---|---|
| S2 | TS Sonnet  | 25 | 25 | **25.0** |
| S6 | TS Sonnet  | 25 | 24 | **24.5** |
| S4 | TS Haiku   | 22 | 22 | **22.0** |
| S8 | TS Haiku   | 21 | 23 | **22.0** |
| S1 | base Haiku | 21 | 21 | **21.0** |
| S3 | base Sonnet| 18 | 20 | **19.0** |
| S5 | base Sonnet| 17 | 20 | **18.5** |
| S7 | base Haiku | 18 | 17 | **17.5** |

- **TOUCHSTONE avg 23.4 vs baseline avg 19.0 → +4.4.**
- **All 4 TOUCHSTONE arms (22.0–25.0) rank strictly above all 4 baselines (17.5–21.0)**
  on the aggregate of both judges. Clean arm separation.
- Both perfect/near-perfect scores were TOUCHSTONE runs that did the Golden-Oracle
  detector move (swap in the spec-correct `(q-1)//10`, show all 9 tests still pass).

## The result: NO discovery gap — again, and now conclusively
**All 8 runs caught the boundary bug — including all 4 baselines, both Haiku and
Sonnet.** Every baseline read `tier = quantity // 10`, reasoned that `10//10=1` puts
q=10 in the wrong tier, computed q=10→4500-vs-5000 and q=20→8000-vs-9000, AND noted
the suite straddles the boundary (9, 11, 21) while skipping 10 and 20. By inspection
+ light mental arithmetic, no discipline.

So across **three bug types × two model strengths** — obvious gaming (v1), a famous
language gotcha (v2), and now a non-famous domain boundary off-by-one (v3) — a
baseline "review this, can we ship?" prompt **never once missed the bug.** The
bug-discovery floor is at the ceiling for single-function artifacts. The reason is
now clear and not model-specific: an artifact this small can be *fully read*, and a
capable model reads its way to the bug. There is nowhere for it to hide.

## Where the +4.4 lives (same as every prior round): Category 5
Cat 1–4 clustered at the top — everyone found the bug, hand-derived the boundary
oracle, mapped the gap, refused green. The entire spread is empirical PROOF:
- Baselines: cat 5 ≈ 1–2. Correct verdict, concrete fix, but *asserted in prose* —
  no mutation, no kill-rate, no swap-in proof.
- TOUCHSTONE: cat 5 ≈ 3–5. Ran mutation batteries with kill-rates and, decisively,
  swapped in the spec-correct implementation to show the suite STILL passes = the
  suite cannot tell buggy code from the fix. Both judges called that the single most
  damning, rubric-prized move. (An independent-eyes sub-agent one TS run spawned
  separately re-confirmed the `(q-1)//10` survivor — external corroboration.)

## Four-round synthesis (the durable, replicated finding)
| Round | Solver | Bug type | TS | Base | Gap |
|---|---|---|---|---|---|
| v1 | Sonnet | obvious gamed suite | 24.5 | 21.0 | +3.5 |
| v2 | Sonnet | famous gotcha (banker's round) | 24.25 | 20.5 | +3.75 |
| v2 | Haiku  | famous gotcha | 24.5 | 18.5 | +6.0 |
| v3 | Sonnet+Haiku | non-famous boundary | 23.4 | 19.0 | +4.4 |

- **TOUCHSTONE ranked above baseline in 8/8 judge cards across 4 rounds. Never reversed.**
- **TOUCHSTONE score is model- and bug-stable (~23.4–24.5 everywhere).** The discipline
  produces consistent test-audit rigor regardless of solver or bug.
- **Baseline score is volatile and lower (17.5–21).**
- **Zero discovery separation in any round.** Bounded conclusively: not produceable on
  single-function artifacts at Haiku-or-stronger.

## Bottom line for TOUCHSTONE's positioning
TOUCHSTONE is a **rigor / proof discipline**, not a bug-finder. Demonstrated value:
it converts "I can see this is wrong" into "I mutated it and proved the suite is
blind" — consistent, quantified, reproducible — and that value is largest where a
model is weakest or an artifact is too large to fully read. It does NOT (and on this
evidence cannot be shown to) help a capable model find bugs it would otherwise miss
at small scale. Claim it for what it is: the lamp that proves the green is hollow,
not a second pair of eyes that sees what the first missed.

## If we ever want to chase a discovery gap (likely diminishing returns)
The only untested regime is a **large / multi-file artifact** where no single function
can be fully reasoned about by inspection, so a bug can hide from a careful reader.
That's a much heavier benchmark to build and run, and the honest expectation after 4
rounds is that the value will still be rigor, not discovery. Recommend stopping here
unless a real multi-file case arises naturally.
