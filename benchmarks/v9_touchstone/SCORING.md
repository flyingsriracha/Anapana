# v9 — TOUCHSTONE benchmark (test-rigor discipline vs baseline)

Does loading TOUCHSTONE before trusting a test suite produce a more rigorous, more
trustworthy assessment than a strong model reviewing tests on its own? Four rounds,
blind dual-judge (Opus + Sonnet), anonymized submissions, /25 rubric. All solvers were
the same model within a round, so the only variable is the discipline.

Each round: a GREEN test suite (passing, ~100% coverage) that hides a real bug. Baseline
arms = "can we trust these tests / ship?"; TOUCHSTONE arms = load + follow the discipline.

## Results
| Round | Solver | Hidden bug | TOUCHSTONE | Baseline | Gap | TS rank |
|-------|--------|-----------|:----------:|:--------:|:---:|---------|
| 1 — obvious gamed suite | Sonnet | tautological tests + a skipped spec test | **24.5** | 21.0 | +3.5 | 1st & 2nd |
| 2 — subtle (famous gotcha) | Sonnet | `round()` is banker's, spec says half-up | **24.25** | 20.5 | +3.75 | 1st & 2nd |
| 2 — subtle (famous gotcha) | Haiku | same | **24.5** | 18.5 | +6.0 | 1st & 2nd |
| 3 — non-famous boundary | Sonnet + Haiku | tier off-by-one (`q//10` vs `(q-1)//10`) | **23.4** | 19.0 | +4.4 | top 4 of 8 |

- **TOUCHSTONE ranked above baseline in all 8 judge cards across the four rounds. Never reversed.**
- **TOUCHSTONE's score is model- and bug-stable (~23.4–24.5 everywhere)**; the baseline's
  is volatile and lower (17.5–21). The discipline produces consistent rigor regardless of
  solver or bug — and it lifts a *weaker* model the most (the Haiku gap is the largest).

## The two honest findings
1. **Rigor, not discovery.** On a small, fully-readable artifact a strong baseline already
   *finds* the bug. The practice's measured value is **empirical proof** — the entire gap
   lives in the rubric's "verdict + depth" category: baselines assert "these tests are
   weak"; TOUCHSTONE *proves it* with a mutation kill-rate and the decisive move below.
2. **No discovery gap was producible** across three bug types × two model strengths — the
   baseline never missed the bug. Likely cause (see canary/contamination note): the
   synthetic bugs are *famous* patterns a strong model recalls. The one contamination-
   resistant signal came from the real-project run (v10), not these fixtures.

## The decisive move (the "Golden Oracle" reveal)
Both judges, every round, singled out the same thing as the strongest evidence: TOUCHSTONE
arms **mutated the code to the spec-correct version and showed the suite still passes** —
proving the suite cannot tell right code from wrong, i.e. its oracle was the code, not the
spec. A gamed suite's tell isn't that it's red; it's that it stays **green for the correct
answer too**. See `GOLDEN_ORACLE_REVEAL.md`.

Detail per round: `round1_obvious.md`, `round2_subtle_sonnet.md`, `round2_subtle_haiku.md`,
`round3_boundary.md`. Caveats: n=2/arm; blind dual-judge; judges are themselves models
(mitigated by anonymization + spread-scoring + two judges, corroborated both ways).
