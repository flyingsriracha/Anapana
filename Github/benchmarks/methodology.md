# Benchmark methodology — how to replicate

This document is a complete protocol for running the ANAPANA benchmarks against
any LLM. It is what was used to produce the numbers in `../report.html`.

---

## Overview

Three benchmark problems, four conditions per problem, optionally multiple
trials per condition. Each trial is a fresh sub-agent (no memory of prior
trials) given identical inputs differing only in which meditation file is
attached.

| Problem | Type | Trials per condition | Codebase |
|---------|------|---------------------|----------|
| **B1** | Pure reasoning (support ops question) | 1 | None |
| **B2** | Code fix, codebase has explicit README documenting invariants | 1 | `test_repos/B2_audit_log/` |
| **B3** | Code fix, codebase has docstrings but no README | 2 (for variance) | `test_repos/B3_async_pool/` |

Conditions:
- **Baseline** — agent gets the problem only, no meditation file
- **BREATH** — agent gets `product/BREATH.md` + the problem
- **INSIGHT** — agent gets `product/INSIGHT.md` + the problem
- **SATORI** — agent gets `product/SATORI.md` + the problem

Run conditions in parallel (each in its own context, no cross-talk). Record
elapsed wall-clock time and token usage per trial.

---

## The problems

### B1 — Support ops reasoning

> Our customer support response time has gotten worse over 6 months. Average
> first-response time went from 4 hours to 11 hours. We hired 2 more support
> agents but it's not helping. What should we do?

This is a *deceptively simple* question. A surface answer ("hire more, improve
tools, automate triage") will sound reasonable but miss the diagnostic
question: **why didn't adding capacity help?** That clue points away from
labor-hours and toward routing / ticket-mix / new-hire ramp tax / measurement
drift / upstream product changes / customer-resubmission feedback loop.

**What separates conditions:** the breadth of lenses, whether the agent leads
with the reframe, and whether it identifies the feedback loop where slow
response itself causes more tickets.

### B2 — Code fix with documented invariants

The codebase is in `test_repos/B2_audit_log/`. The bug report is in
`test_repos/B2_audit_log/BUG_REPORT.md`:

> When our subscription-cancellation worker auto-refunds the unused portion of
> a canceled subscription, `payments/charge.py:process_refund` is called with
> `initiated_by=None` (system-initiated refund, no human user). `AuditLog.log_event`
> crashes with `AttributeError: 'NoneType' object has no attribute 'id'`.
> The refund succeeds at the provider, but our function returns 500, the worker
> retries, and we get duplicate refunds. Please fix so refunds work for both
> user-initiated and system-initiated cases.

**The trap:** the obvious fix (make `log_event` accept `actor=None` and write
`actor_id=NULL`) breaks a security invariant documented in the README and used
by `admin/user_actions.get_anonymous_failed_logins` for credential-stuffing
detection. The right fix is in `payments/charge.py` — substitute a `SYSTEM_ACTOR`
sentinel, leave the shared utility alone.

**What separates conditions:** whether the agent reads the README, whether it
catches the silently-broken security dashboard (`auth/login.py` swallows the
audit AttributeError so no failed-login rows are ever written), and whether it
verifies the README's claims independently.

### B3 — Code fix with no README

The codebase is in `test_repos/B3_async_pool/`. The bug report is in
`test_repos/B3_async_pool/BUG_REPORT.md`:

> The `/dashboard` endpoint times out at 30 seconds in production. The underlying
> SQL queries are fast — running them directly in psql against the production
> DB takes under 8 seconds total. Tests pass locally. We have a board meeting
> Friday and the dashboard needs to work. The fastest fix is preferred. Please
> look at `reports/dashboard.py` and get it returning under 30s.

**The trap (intentional):**
- The prompt explicitly points at `reports/dashboard.py` — the wrong file
- "Fastest fix Friday" pressure pushes toward symptom fixes
- The dashboard code is correct; the bug is in `tasks/nightly_export.py` (early
  return without releasing the connection) AND in `db/pool.py:acquire_raw`
  (no try/except around `_create_connection`, so semaphore leaks if connection
  creation throws)
- Tests pass because the test fixture creates an isolated pool that never
  exercises the contention

**What separates conditions:** whether the agent reads other files, resists the
"look at dashboard.py" framing, finds the leak in `nightly_export.py`, and
optionally builds a reproduction harness that finds the second (unplanted) leak
in `acquire_raw`.

---

## The agent prompt template

Use the four prompt files in `agent_prompts/`:

- `agent_prompts/baseline.md`
- `agent_prompts/breath.md`
- `agent_prompts/insight.md`
- `agent_prompts/satori.md`

Each is a complete, self-contained prompt. Replace `{PROBLEM}` with the
problem text from above and `{CODEBASE_PATH}` with the test repo path. The
BREATH/INSIGHT/SATORI prompts have the corresponding meditation file content
already inlined.

**Required output format** (same across all conditions) is documented at the
bottom of each prompt — START_TS / DIAGNOSIS / PROPOSED_FIX / END_TS, etc.

---

## Scoring rubric

See `scoring_rubric.md`. Seven main dimensions plus two V3-specific ones,
each scored 1–5 by reading the agent's report. The dimensions:

1. Surface bug correctness
2. Bigger-picture awareness
3. Considered consumers / dependencies
4. Preserved system invariants
5. Hidden issues found (issues user didn't mention)
6. Resisted grasping / framing pressure
7. Confidence calibration
8. Reproduction executed (SATORI metric)
9. Doc-led flag (SATORI metric)

---

## Recommended sample sizes

| Goal | Per-condition trials |
|------|---------------------|
| Quick directional check | 1 |
| Variance check on a single problem | 2–3 |
| Publishable comparison | 5+ |

This benchmark used 1 trial each for B1 and B2 and 2 trials each for B3, total
of 16 trials. Single trials are noisy — the directional findings (SATORI is
faster than INSIGHT, INSIGHT finds more hidden issues than Baseline) are robust,
but exact ratios should be treated as estimates.

---

## Costs observed (Claude Sonnet 4.6, this benchmark)

| Condition | Avg time | Avg tokens |
|-----------|---------:|-----------:|
| Baseline | 28 s | 22.8 k |
| BREATH | 150 s | 28.9 k |
| INSIGHT | 192 s | 33.3 k |
| SATORI | 91 s | 30.2 k |

If running on a different model, expect substantially different numbers.
GPT-4o tends to skip steps. Smaller models (under ~70B) will treat the
checklist as decorative.

---

## Files in this directory

- `methodology.md` — this file
- `scoring_rubric.md` — the 1-5 scoring criteria
- `problems/B1.md`, `B2.md`, `B3.md` — full problem statements
- `agent_prompts/` — the four prompt templates
- `results_data.json` — the raw measurements that drive the charts in
  `../report.html`. Copy this format if you want to plug your own data
  into the same report template.
- `../test_repos/` — the codebases for B2 and B3
- `../benchmarks/B{1,2,3}_*/` — the actual agent reports from this run

---

## How to add a new condition (e.g., your own variant of the meditation file)

1. Create a new prompt file at `agent_prompts/your_variant.md` based on the
   `satori.md` template, with your variant's content inlined.
2. Run agents on B1, B2, B3 (recommend 2 trials each).
3. Score using the rubric.
4. Add a new entry to `results_data.json` under your variant's key.
5. Update the `DATA.conditions` array in `../report.html` to include your
   variant. The charts will pick it up automatically.

---

## How to add a new problem (a 4th benchmark)

1. Write a problem statement. If it's a code fix, create a test repo at
   `../test_repos/B4_your_problem/` with a `BUG_REPORT.md`.
2. Run all four conditions against it.
3. Score and add to `results_data.json` as `B4`.
4. Update `DATA.benchmarks` in `report.html`.

The benchmark improves with diversity. Strong candidates for new problems:
prompts with no obvious framing pressure (different from B3), prompts with
heavy domain expertise required, prompts where the right answer is genuinely
"I don't know — ask the user."
