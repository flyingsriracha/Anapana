# SATORI-Lite v3.2 + clean B2 fair-rerun — results

Second pass: B2 with properly buggy state (both audit_log.py AND charge.py
reverted) and SATORI-Lite v3.2 with mandatory reproduction.

## B2 clean rerun (all 4 conditions)

| Cell | Tokens | Wall | Surface | Repro | Doc-led | Identity | Hidden issue |
|------|-------:|-----:|--------:|------:|--------:|---------:|-------------:|
| Baseline | 26.9k | 191s | 5 (sentinel + guard + try/except removed) | 1 (none run) | 5 | 4 | 5 (removed try/except in fix) |
| BREATH | 25.8k | 215s | 5 (sentinel approach) | 2 (described not run) | 5 | 4 | 5 (called out) |
| INSIGHT | 29.7k | 217s | 5 (sentinel id=0) | 2 (smoke test described) | 5 | 5 | 4 (acknowledged) |
| SATORI-Lite v3.2 | 24.3k | 191s | 5 (NULL-safe verified via cross-module check) | **5 (actually ran)** | 5 | 4 | 4 (acknowledged) |

**Findings:**
- **Baseline produced the highest-quality fix in this rerun**, including removing
  the auth/login.py try/except — better than its original B2 trial. The README
  is so prescriptive that even Baseline produces the doc-led answer. The B2
  benchmark is now arguably *too easy* for the model — the docs do almost all
  the work.
- **SATORI-Lite v3.2's reproduction discipline returned.** It actually ran code
  before proposing and verified the fix worked. v3.1 trials had skipped this.
- INSIGHT's fix (sentinel id=0) is cleaner than Baseline's (sentinel id="system");
  Baseline produced a textually-correct but more brittle solution.

## SATORI-Lite v3.2 × B3 (2 trials)

| Cell | Tokens | Wall | Surface | Repro | Tier picked | Identity |
|------|-------:|-----:|--------:|------:|------------|---------:|
| Trial 1 | 23.0k | 133s | 5 (try/finally fix) | **5 (ran 10× pool exhaustion test, confirmed)** | STANDARD | 5 |
| Trial 2 | 37.1k | 356s | 5 (try/finally fix) | **5 (ran semaphore exhaustion + TimeoutError repro)** | STANDARD | 5 |

**Findings:**
- **Both trials ran actual reproductions.** v3.1 trials skipped this; v3.2 fix
  ("code-visible NOT sufficient grounds") successfully restored the discipline.
- **Cost went up substantially.** v3.1 B3 average was 17.0k / 66s; v3.2 B3
  average is 30.1k / 245s — almost back to original SATORI's 33.2k / 117s.
- **Neither v3.2 trial found the deeper acquire_raw bug.** Even with
  reproduction discipline restored, the agents built reproductions that
  exercised the planted leak, not the hidden one. The original v2/v3
  SATORI trials that caught acquire_raw built `FaultyPool` subclasses —
  a specific pattern the SATORI-Lite agents didn't reach for.

## Cost comparison: SATORI vs SATORI-Lite v3.1 vs v3.2

| Benchmark | SATORI | Lite v3.1 | Lite v3.2 |
|-----------|------:|----------:|----------:|
| B1 (avg) | 25.2k / 104s | 13.9k / 49s | 13.9k / 49s* |
| B2 | 32.2k / 51s | 21.5k / 127s | 24.3k / 191s |
| B3 (avg) | 33.2k / 117s | 17.0k / 66s | 30.1k / 245s |
| **Mean** | **30.2k / 91s** | **17.5k / 80s** | **22.8k / 162s** |

\* B1 was not rerun for v3.2 because there's no codebase — the reproduction
mandate doesn't apply.

**SATORI-Lite v3.2 saves ~25% tokens vs SATORI** with reproduction discipline
intact. v3.1 saves ~42% tokens but at the cost of the reproduction step.

## The actual trade-off

The big token win in v3.1 came mostly from skipping reproduction, not from
the triage/tiered-depth system. With reproduction restored as a hard
requirement, the savings collapse from ~42% to ~25%.

Two reasonable positions:

**Position A — keep v3.2 (recommended).** Reproduction is the highest-value
step in the practice; trading it for ~17 percentage points of token savings
is a bad deal. v3.2 still saves real tokens via tiered depth and SKIP for
trivial work.

**Position B — make reproduction conditional on stakes, not on availability.**
"Run code when (a) the codebase is accessible AND (b) the diagnosis is not
fully derivable from a single grep, AND (c) the cost of being wrong is >10×
the cost of running 50 lines of Python." This recovers most of v3.1's
savings while preserving the discipline where it matters.

Position B introduces a judgment call the agent has to make; Position A
makes it a rule. Rules survive contact with token pressure better than
judgment calls.

## Setup mutation caveat

Sub-agents ran reproductions that involved *applying their proposed fixes*
to the buggy copies on disk (`/tmp/B2_audit_log_buggy/utils/audit_log.py`
got the None-guard written by SATORI-Lite v3.2; `/tmp/B3_async_pool_buggy/
tasks/nightly_export.py` got the try/finally written by a SATORI-Lite v3.2
B3 trial). The 4 parallel B2 agents all read the buggy state before any
of them wrote — confirmed by checking each report's cited line numbers and
crash locations. Subsequent reruns from /tmp/ would need re-reverting.

## Recommendation

1. Adopt SATORI-Lite v3.2 as the new recommended file (replaces SATORI).
2. Use original SATORI as the "deep" tier for cross-cutting design work
   (10-min budget tasks where the FULL variance discipline matters).
3. Keep BREATH and INSIGHT as the lower stages (subsume relationship
   unchanged: BREATH → INSIGHT → SATORI-Lite → SATORI).
4. The new gradient: pause and reframe (BREATH) → frame check (INSIGHT) →
   triage+reproduce+identity (SATORI-Lite) → full pre-decision rigor (SATORI).

Or — if simplicity matters more — replace SATORI v3 with SATORI-Lite v3.2
and don't maintain two SATORI variants. The marginal value of the FULL
SATORI over Lite v3.2 isn't clearly worth the cognitive overhead of a
4th stage.
