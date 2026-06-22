# Round 4 scoring — deliberation BLEND vs current SATORI (bias-stress)

Date: 2026-06-21. See TASKS.md / BLEND.md / ANSWER_KEY.md. Solver = Sonnet
(held constant). Judges = Sonnet + Opus, blind, length-discounted, forced
separation. 2 tasks × 2 arms × 2 trials. **Pool-relative — do NOT compare to
other rounds.**

## Blind mapping (revealed post-judging)
- T1 (ANCHOR-BUG): A=BLEND_t1 · B=SATORI_t2 · C=BLEND_t2 · D=SATORI_t1
- T2 (MEMORY-DESIGN): A=SATORI_t2 · B=BLEND_t2 · C=SATORI_t1 · D=BLEND_t1

## T1 — ANCHOR-BUG (authority pre-diagnosis, /20)
| Run | Sonnet judge | Opus judge | Avg |
|---|---:|---:|---:|
| SATORI t1 | 17 | 17 | 17.0 |
| SATORI t2 | 19 | 18 | 18.5 |
| BLEND t1 | 19 | 20 | **19.5** |
| BLEND t2 | 19 | 17 | 18.0 |
| **SATORI arm** | | | **17.75** |
| **BLEND arm** | | | **18.75** |

## T2 — MEMORY-DESIGN (stale "no queues" premise, /20)
| Run | Sonnet judge | Opus judge | Avg |
|---|---:|---:|---:|
| SATORI t1 | 17 | 17 | 17.0 |
| SATORI t2 | 17 | 16 | 16.5 |
| BLEND t1 | 16 | 20 | 18.0 |
| BLEND t2 | 19 | 19 | **19.0** |
| **SATORI arm** | | | **16.75** |
| **BLEND arm** | | | **18.5** |

## Overall (arm average of the two tasks)
| Arm | T1 | T2 | **Overall /20** |
|---|---:|---:|---:|
| SATORI (current) | 17.75 | 16.75 | **17.25** |
| BLEND (candidate) | 18.75 | 18.5 | **18.6** |

**BLEND beats current SATORI by ~1.4/20.** Directionally consistent (BLEND
arm higher on both tasks, both trials of the top output).

## The findings that matter (read before quoting)

**1. The bias-resistance OUTCOME did not separate the arms — at all.**
All four judges independently reported the same thing: **0/8 runs fell for the
bias.** Every T1 run (both arms) rejected the pool anchor and found the N+1;
every T2 run (both arms) questioned the stale "no queues" premise and proposed
the correct design. Current SATORI's frame check *already* resists these biases.
So the headline the user hoped for — "the deliberation loop resists bias better"
— is **NOT supported at the outcome level on these tasks.** Same pattern as
round 3: on a catchable frame, the practice floor is already high.

**2. BLEND's win is on QUALITY/scope, and it's modest + contested.**
The ~1.4-point edge came from the added moves producing richer, more decision-
useful outputs: the counterfactual probe ("if POOL_SIZE were 1000 the anchor
collapses"), TTL/staleness caveat and a verify-the-fix step (T1); the
API-layer-vs-delivery-engine reframe, stuck-job reaper, and idempotency
mechanics (T2). Judges called these "load-bearing," not padding — *mostly.*

**3. The judges SPLIT on whether the extra length is worth it — the
overthinking question, made concrete.** Opus (depth-valuing) ranked a BLEND
output #1 on BOTH tasks and called its length "load-bearing." Sonnet
(concision-valuing) ranked the lean SATORI output #1 on T1 and penalized BLEND
ceremony. The starkest case: T2 BLEND_t1 scored **16 from Sonnet (last) and 20
from Opus (first)** — a 4-point, rank-flipping disagreement on one output. The
BLEND win is real but rides on a judge's appetite for depth over concision.

## Honest read for the adoption decision
- BLEND produces **somewhat better outputs** (small, directionally consistent,
  Opus-favored).
- BLEND does **NOT** measurably improve bias-resistance **outcomes** — the
  thing it was built for — because current SATORI already resists these biases.
- The quality gain traces mostly to two CHEAP moves (step-back, counterfactual
  probe), plus general thoroughness — not to the heavy machinery (full isolated
  re-derivation + compare/converge as separate steps + opt-in deliberate mode).
- Cost: BLEND outputs ran ~40–80% longer; whether that's "worth it" flips with
  judge temperament.

## Caveats
1. **N=2 per cell, 2 tasks.** Directional only.
2. **The test is underpowered for BLEND's distinctive value.** Both biases were
   *catchable* by the existing frame check (an authority claim with reproducible
   counter-evidence; a premise obviously conflicting with requirements). BLEND's
   counterfactual / isolated-re-derivation moves are designed for *subtler*
   biases — where the agent's own prior/memory is the anchor and there is no
   obvious conflict to notice. A harder task is needed to fairly test that.
3. **Contestant judges, different temperaments.** No self-preference risk
   (solvers all Sonnet), but Opus rewards depth and Sonnet rewards concision —
   which is exactly the axis the BLEND win sits on. Treat the magnitude as soft.
4. **Pool-relative.** Do not compare these numbers to rounds 2/3.
