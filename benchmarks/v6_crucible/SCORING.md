# Round 6 scoring — CRUCIBLE vs uncalibrated baseline (adversarial review)

Date: 2026-06-22. Validates the CRUCIBLE red-team meditation. Solver = Sonnet.
Arms: BASELINE ("be thorough and adversarial, find everything") vs CRUCIBLE
(load CRUCIBLE.md). One artifact (`artifact_password_reset.md`) with planted
real issues + nits + a suppression trap + a rewrite bait. 2 arms × 2 trials =
4 runs, blind dual judges (Sonnet + Opus), rubric /25. Pool-relative.

## Blind mapping (revealed post-judging)
A = CRUCIBLE_t1 · B = BASELINE_t2 · C = CRUCIBLE_t2 · D = BASELINE_t1

## Scores (/25: Recall, SecElev, Noise-control, Whole-system, Resisted-traps)
| Run | Sonnet | Opus | Avg |
|---|---:|---:|---:|
| CRUCIBLE t1 | 23 | 22 | 22.5 |
| CRUCIBLE t2 | 22 | 24 | 23.0 |
| BASELINE t1 | 17 | 15 | 16.0 |
| BASELINE t2 | 16 | 20 | 18.0 |
| **CRUCIBLE arm** | | | **22.75** |
| **BASELINE arm** | | | **17.0** |

**CRUCIBLE > BASELINE by +5.75/25.** Clean separation: BOTH judges ranked BOTH
CRUCIBLE runs above BOTH baseline runs (Sonnet: A,C,D,B; Opus: C,A,B,D).

## The finding
Both judges independently: the difference is **CALIBRATION, not recall.** All
four runs caught the real bugs (token forgery, log/URL leak, shared-queue,
lifetime rate-limit counter). They separated on:
- **Noise control** — CRUCIBLE tiered findings (Block/Sprint/Backlog/Hypothesis)
  and dropped the nits; BASELINE produced 17–20-item near-flat walls with `e`,
  marketing copy, JSON-bool, and speculative CSRF/HTTPS inflated to HIGH.
- **Security elevation** — CRUCIBLE kept the token bug as the clear blocker;
  BASELINE buried it among many co-equal HIGHs.
- **Traps** — CRUCIBLE explicitly set aside the "approved" banner and declined
  the OAuth-rewrite bait (fix-in-place); a baseline run surfaced the rewrite
  question as an open item (scope-creep).
This is the over-aggression failure the file was built to fix — and it fixed it.

## Weakness the benchmark exposed (one refinement indicated)
CRUCIBLE_t1 demoted the **whole-system shared-queue** finding to "hypothesis"
(Opus docked it Whole-system 3 — understating a real, mechanism-clear flaw).
CRUCIBLE_t2 handled it correctly (ranked it + reasoned the blast radius;
Whole-system 5) under the SAME file → within-arm variance, not a hard defect.
Indicated tuning: the step-6 grounding gate should NOT demote an adjacent-system
finding with a clear mechanism to "hypothesis" merely for lacking load numbers —
flag it as a real finding tagged "confirm at scale." Optional one-line nudge.

## Caveats
1. N=2/cell, 1 artifact — directional, but the separation is clean and
   replicated by both judges.
2. Contestant judges (no neutral model); mitigated by blind anonymization,
   length-discount, force-separation, dual judges. Both agreed on arm ordering.
3. Baseline = a realistic "be thorough/adversarial" red-team prompt (the common
   status quo), not a strawman — that prompt is what produces over-flagging.
4. Pool-relative; do not compare to other rounds.
