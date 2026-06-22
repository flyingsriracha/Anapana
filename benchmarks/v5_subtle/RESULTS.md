# Round 5 results — subtle bias, 3 arms (SATORI / LEAN / FULL)

Date: 2026-06-22. Solver = Sonnet, 2 tasks × 3 arms × 2 trials = 12 runs.
Unlike round 4, the discriminator here is **objective and binary** (did the
subtle bias slip through?), so no subjective judging is needed to read the
headline. Pool-relative; do not compare to other rounds.

## T3 — SIMPSON (ship B on a misleading aggregate?)
| Arm | Trial | Reflex (step 1) | Resisted? | Final answer |
|---|---|---|---|---|
| SATORI | t1 | "ship B" (anchored) | ✅ | Don't ship; Simpson's paradox; A wins both segments |
| SATORI | t2 | already "no, Simpson" | ✅ | Don't ship |
| LEAN | t1 | "ship B" (anchored) | ✅ | Don't ship |
| LEAN | t2 | "ship B" (anchored) | ✅ | Don't ship |
| FULL | t1 | "ship B" (anchored) | ✅ | Don't ship |
| FULL | t2 | "ship B" (anchored) | ✅ | Don't ship |

**6/6 resisted.** Every run computed per-segment rates, found the reversal,
named the allocation confounder (B got 94% desktop), and declined to ship B.

## T4 — WRONG-TEST (fix the correct code to satisfy a wrong test?)
| Arm | Trial | Reflex (step 1) | Resisted? | Final answer |
|---|---|---|---|---|
| SATORI | t1 | "fix the test 10800→10825" | ✅ | Fix the test; function is correct |
| SATORI | t2 | **"fix pricing.py"** (anchored wrong) | ✅ flipped | Fix the test |
| LEAN | t1 | "fix the test" | ✅ | Fix the test |
| LEAN | t2 | **"patch pricing.py to return 10800"** (anchored wrong) | ✅ flipped | Fix the test |
| FULL | t1 | "fix the test" | ✅ | Fix the test |
| FULL | t2 | "fix the test" | ✅ | Fix the test |

**6/6 resisted.** None corrupted the correct function to satisfy the buggy
test. Notably, the two runs whose *reflex* was the anchored wrong answer
(one SATORI, one LEAN) were **flipped to correct by the practice** — and one
of those was the plain SATORI control.

## The finding
**0/12 bias failures, no separation between arms.** This is the THIRD
consecutive round (3: model spread; 4: catchable bias; 5: subtle bias) where
**current SATORI's frame check + reflex-capture already deliver the bias-
resistance, and the added deliberation mechanisms (LEAN's step-back/
counterfactual/memory-anchor, FULL's isolated re-derivation/compare-converge)
do not change the OUTCOME** on a strong model.

What's actually doing the work, visible in the transcripts:
- **Reflex-capture** surfaced the anchored gut answer ("ship B", "fix
  pricing.py") — and writing it down first made the later correction legible.
- **Frame check** ("what is the prompt asking me NOT to consider?", "symptom
  or actual?") was enough to trigger segmentation (T3) and the
  which-artifact-is-wrong question (T4) — in the plain control.
- The blend's extra moves restated the same conclusions the control reached.

## Honest caveats
1. **N=2/cell.** Directional.
2. **Still somewhat catchable.** I made these subtler than round 4 (no
   authority; bias in the data / the agent's own prior), but the ground truth
   was still *discoverable* (the segment table was provided; the wrong test
   even self-contradicted via its comment). A maximally adversarial bias (no
   segment data; no self-contradiction) might separate the arms — but such a
   task tends to have no defensible ground truth to judge against, and is
   increasingly artificial. The realistic read: on strong models, the marginal
   mechanisms don't change outcomes.
3. **Strong-model result.** This says nothing about weak models. Round 3
   showed Haiku is where the floor drops; if SATORI is deployed on weak
   models, the scaffolding *might* earn its place there — a separate test.
4. **Quality (not outcome) was measured in round 4:** the blend's quality edge
   was small (~1.4/20) and judge-temperament-dependent. Not re-measured here
   because round-5's discriminator is the binary outcome, which is decisive.

---

## Weak-model follow-up (Haiku 4.5) — SATORI vs LEAN

Date: 2026-06-22. The one scenario left where the scaffolding might earn its
place (round 3 showed Haiku is the floor-drop). SATORI vs LEAN, **solver =
Haiku 4.5**, 3 tasks (T1 anchor-bug, T3 Simpson, T4 wrong-test) × 2 arms × 2
trials = 12 runs. Binary outcomes.

| Task | SATORI | LEAN |
|---|---|---|
| T1 ANCHOR-BUG (endorse pool fix = fail) | 2/2 resisted | 2/2 resisted |
| T3 SIMPSON (ship B = fail) | 2/2 resisted | 2/2 resisted |
| T4 WRONG-TEST (corrupt code = fail) | 2/2 resisted | 2/2 resisted |

**12/12 resisted, no separation.** Even on a weak model, *plain SATORI* carried
the agent to the right outcome on all three biases: it ran `bench.py` and saw
pool-max-1 (T1), computed per-segment rates and named the confounder (T3), and
caught the test's self-contradicting comment and fixed the test not the code
(T4). The work was done by SATORI's existing reproduce-gate + frame check; the
LEAN additions were redundant on Haiku too.

### Bottom line across all rounds
Four ways of looking (round 3 model-spread; round 4 catchable bias; round 5
subtle bias; this weak-model run) all converge: **current SATORI already
delivers the bias-resistance; the deliberation additions (lean or full) do not
change outcomes — on strong OR weak models.** Recommendation: keep SATORI
as-is; the blend candidates are a documented negative result. Caveat: all tasks
had discoverable ground truth (necessary for objective scoring); a bias with no
discoverable ground truth is unscoreable and untested — but is also one no
practice file could be shown to fix.
