# v3 bake-off — scoring & verdict

Date: 2026-06-04. 12 runs: 4 conditions (v2, ANCHOR, COMPASS, LANTERN) ×
3 benchmarks (B1 reasoning, B2 code+README, B3 code+framing-trap). Single
trial per cell. Held-constant model (sonnet). Fixes proposed text-only
(no file edits → no parallel-mutation corruption).

## Raw results

| Cell | Tier | Surface | Hidden* | Repro | Tokens |
|------|------|--------:|--------:|-------|-------:|
| v2 × B2 | STANDARD | ✓ (5) | 2 | ran | 22.8k |
| ANCHOR × B2 | frame+repro | ✓ (4) | 3 | confirmed | 20.4k |
| COMPASS × B2 | STANDARD | ✓ (5) | 2 | ran | 20.8k |
| LANTERN × B2 | FULL | ✓ (5) | 3 | ran | 22.4k |
| v2 × B3 | STANDARD | ✓ | 2 | confirmed | 25.1k |
| ANCHOR × B3 | T1+T2 | ✓ (5) | 3 | confirmed | 19.6k |
| COMPASS × B3 | FULL | ✓ | 3 | confirmed | 20.6k |
| LANTERN × B3 | STANDARD | ✓ | 3 | confirmed | 19.7k |
| v2 × B1 | FAST | 4 | 3 | externalized | 17.6k |
| ANCHOR × B1 | frame-only | 3 | 2 | n/a | 14.9k |
| COMPASS × B1 | FULL | 4 | 3 | n/a | 16.0k |
| LANTERN × B1 | STANDARD | 4 | 4 | n/a | 17.2k |

\* Hidden-issue counts are **self-reported by the agents** — treat as
soft signal, not hard data (this is exactly the unreliable self-grading
the research flagged). The hard signals are surface-correctness (did it
find the real bug and resist the B3 framing trap — verifiable) and tokens
(measured).

## Aggregates

| Condition | Total tokens | Code tokens (B2+B3) | Resisted B3 trap | All surface fixes correct |
|-----------|------------:|--------------------:|:----------------:|:-------------------------:|
| v2 | 65.5k | 47.9k | ✓ | ✓ |
| **ANCHOR** | **54.9k** | **40.0k** | ✓ | ✓ |
| COMPASS | 57.4k | 41.4k | ✓ | ✓ |
| LANTERN | 59.3k | 42.1k | ✓ | ✓ |

## What the hard data says (discounting self-reported hidden counts)

1. **All four resisted the B3 framing trap and fixed B2.** Surface
   correctness is a TIE. The frame check — present in all four designs —
   is doing the work. This re-confirms the central research finding: the
   frame check is the differentiator, and it's cheap.
2. **On code (B2+B3), there is no quality difference between designs** —
   all four found the real bugs and resisted misdirection. The only
   separator is cost, and **ANCHOR is cheapest (40.0k vs 41.4 / 42.1 /
   47.9).** Minimalism wins on code.
3. **LANTERN's heavy verification machinery bought nothing on code** —
   same correctness as ANCHOR at higher cost. The rigor did not pay.
4. **v2 is the most expensive everywhere** and never the most correct —
   the accretion the audit warned about, now measured.

## The one real nuance (soft signal)

On **B1 (open-ended reasoning, no code ground-truth)**, the heavier
designs surfaced more angles: LANTERN found 4 self-reported hidden
issues, COMPASS/v2 found 3, **ANCHOR found the fewest (2)** and rated its
own surface answer lowest (3/5). So where there is no reproduction to
converge on, depth may help — but this rests on noisy self-report and a
single trial.

## Tier-calibration observations
- ANCHOR fired frame-only on B1 — appropriately light, but thin.
- COMPASS picked FULL on B1 (a reasoning task) — mild over-tiering.
- LANTERN picked STANDARD on B1/B3 — well-calibrated.

## Verdict (against the pre-committed decision rule)

Rule: *best quality-per-token on code benchmarks with non-trivial delta;
if ANCHOR matches the heavier designs, minimalism wins; ties to lighter.*

**By the rule, ANCHOR wins.** On code it matched (arguably beat) every
heavier design on verifiable correctness, at the lowest cost, with a
real reflex→proposal delta in every cell.

**Honest blind spot in the rule:** it under-weighted reasoning, where
ANCHOR was weakest. So:
- If ANAPANA is used mostly on **code / debugging** → **ANCHOR.**
- If it spans **open-ended reasoning / design** too → **COMPASS** is the
  safer all-rounder (matched ANCHOR on code, stronger on B1, modest cost).
- **LANTERN is ruled out either way** — its rigor only helped on reasoning,
  and not enough to justify being the most ritual-heavy design (the exact
  "performs the verification without changing the answer" risk).

## Caveats
- Single trial per cell. B3 was NOT close (all converged) so no trial-2
  needed there; B1 differences are small and self-report-driven — do not
  over-weight.
- Hidden-issue counts are agent self-reports; the robust conclusion rests
  only on surface-correctness (tie) + tokens (ANCHOR lowest).
- v3.2 was not re-run this batch; its prior numbers are a different
  session/model and not directly comparable.
