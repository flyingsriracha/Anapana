# SATORI-Lite (v3.1) — benchmark results

Compared against original SATORI numbers from `results_data.json`.
SATORI-Lite ran 2 trials per benchmark on the same B1/B2/B3 problems,
buggy-state copies at `/tmp/B2_audit_log_buggy/` and
`/tmp/B3_async_pool_buggy/`. Sonnet via sub-agents.

## Cost (the headline)

| Benchmark | Original SATORI tokens | SATORI-Lite tokens | Δ | Original SATORI time | SATORI-Lite time | Δ |
|-----------|----------------------:|-------------------:|--:|---------------------:|-----------------:|--:|
| B1 | 25.2k | 13.9k (avg) | **−45%** | 104s | 49s (avg) | **−53%** |
| B2 | 32.2k | 21.5k (avg) | **−33%** | 51s | 127s (avg) | **+149%** |
| B3 | 33.2k (avg) | 17.0k (avg) | **−49%** | 117s (avg) | 66s (avg) | **−44%** |
| **Mean** | **30.2k** | **17.5k** | **−42%** | **91s** | **80s** | **−12%** |

Token reduction met the proposal's "50–60% of current SATORI" target.
Wall-clock improved on B1/B3; B2 trial 2 ran 173s (one outlier — the
other B2 trial was 80s).

## Tier selection (the triage worked)

Six trials picked tiers as follows:

| Trial | Picked | Should have picked |
|-------|--------|-------------------|
| SAT-L × B1 t1 | STANDARD | FAST or STANDARD (reasonable) |
| SAT-L × B1 t2 | SKIP (then did full work anyway) | STANDARD ideally — SKIP is wrong for "what should we do?" |
| SAT-L × B2 t1 | STANDARD | STANDARD ✓ |
| SAT-L × B2 t2 | STANDARD | STANDARD ✓ |
| SAT-L × B3 t1 | FULL | STANDARD or FULL (defensible) |
| SAT-L × B3 t2 | STANDARD | STANDARD ✓ |

**Calibration issue.** B1 trial 2 declared SKIP — none of T1/T2/T3 fired
— but then produced a full FRAME_CHECK + MEDITATION_TRACE + IDENTITY
checkpoint + proposal anyway. The agent interpreted "SKIP" as "skip the
practice, but still answer using the report format". The SKIP path
needs clearer instructions: "write a 2-line report and stop."

**Triage as a forcing function worked when used honestly.** STANDARD
tier trials reliably ran 4–6 of the 8 steps, not 8. The FULL trial
ran all 8. This is the tiered-depth payoff.

## Quality

| Cell | Correct surface fix | Identity differed | Reproduction run | Hidden issue caught |
|------|--------------------:|------------------:|-----------------:|--------------------:|
| SAT-L × B1 t1 | ✓ "ask for data first" | ✓ | n/a (reasoning) | ✓ feedback-loop framing |
| SAT-L × B1 t2 | ✓ "ask for data first" | ✓ | n/a | ✓ feedback-loop framing |
| SAT-L × B2 t1 | ✓ (caught code/README mismatch + auth) | ✓ | partial (described, not run) | ✓ auth/login.py |
| SAT-L × B2 t2 | ✓ same finding as t1 | ✓ | ✓ (ran simulated code) | ✓ auth/login.py |
| SAT-L × B3 t1 | ✓ try/finally fix | ✓ | ✗ inspection only | ✗ acquire_raw missed |
| SAT-L × B3 t2 | ✓ async-with refactor | ✓ | ✗ inspection only | ✗ acquire_raw missed |

**All 6 surface fixes correct.** All 6 identity checks fired.

**The reproduction step degraded.** Both B3 SATORI-Lite trials skipped
reproduction, calling the bug "deterministic and code-visible." The
original SATORI B3 trials built `FaultyPool` harnesses and that's how
they found the second acquire_raw bug — which SATORI-Lite missed.

**Trade-off surfaced:** the reproduce-first override I designed was
intended to use the repro to SKIP later steps, but it also gave agents
license to skip the repro itself when they felt the diagnosis was
already clear. Net effect on B3: faster, cheaper, but no deeper-bug
discovery.

## Caveat on B2 setup

The B2 buggy-state copy was *partially* buggy — I reverted
`payments/charge.py` to remove its SYSTEM_ACTOR usage but
`utils/audit_log.py` already had the `_SystemActor` sentinel fix
(carried over from the original `test_repos/B2_audit_log/`). So the
crash described in `BUG_REPORT.md` doesn't reproduce in the test
fixture — the code already handles `actor=None`.

This is itself a quality signal. Both SATORI-Lite B2 trials *noticed*
the mismatch (the bug report says "crashes" but the code doesn't) and
diagnosed the real remaining bug: `auth/login.py`'s stale try/except
silently routes failed logins through `log_event(actor=None)` → writes
`actor_id="system"` → breaks credential-stuffing detection. That's a
deeper finding than the original SATORI B2 made.

For a clean re-comparison the buggy state needs both files reverted.

## What the data says about the SATORI-Lite proposal

**Confirmed:**
1. Triage + tiered depth saves ~40% tokens on average — close to the
   ~50% upper bound from the proposal.
2. Identity checkpoint as a gate still fires reliably (6/6).
3. File compression didn't break anything — agents followed the leaner
   instructions cleanly.

**Refuted / needs revision:**
1. **Reproduce-first override is a double-edged sword.** Agents used
   it to skip reproduction entirely, not to short-circuit later steps.
   Fix: make reproduction *mandatory* when codebase is available, and
   make "code-visible" an unacceptable reason to skip it.
2. **SKIP needs an explicit "stop now" instruction.** B1 trial 2
   declared SKIP and proceeded to do everything anyway. Fix: "If
   SKIP, write 2-line report (problem + answer) and stop."
3. **Trace cap not always respected.** Several trials wrote multi-
   paragraph step traces. Not a deal-breaker — output tokens dropped
   anyway from fewer steps — but the "one sentence per step" cap
   needs to be a hard constraint, not a soft preference.

## Recommended SATORI-Lite v3.2 deltas

1. Replace the SKIP description with:
   "SKIP → Write `## ANSWER` followed by the answer, in ≤3 sentences.
    Do not write any other report sections. Stop."
2. Replace reproduce-first with reproduce-required:
   "If language supports running code, RUNNING the reproduction is
    mandatory before proposing. 'Code-visible' is not sufficient
    grounds to skip — the repro is what catches the bugs reasoning
    missed."
3. Make trace cap explicit:
   "Each step in MEDITATION_TRACE: exactly one citation-bearing
    sentence. If you need a paragraph, the step surfaced a reframe —
    flag it and put the detail in FRAME_CHECK section, not the trace."

## Verdict

SATORI-Lite delivers the token reduction with quality intact on the
surface fix and identity dimensions. The reproduction-discipline
regression is real and addressable. v3.2 with the three fixes above
would land the proposal cleanly.

## Suggested next step

Apply the v3.2 deltas to `product/SATORI_LITE.md` and rerun the 2
B3 trials only (to verify reproduction discipline returns). If both
trials now run reproductions AND keep the lower token count,
SATORI-Lite is ready to replace SATORI as the recommended file.
