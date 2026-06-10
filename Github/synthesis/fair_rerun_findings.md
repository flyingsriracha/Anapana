# Fair rerun — findings (B2 + B3, Baseline/BREATH/INSIGHT with SATORI report format)

Run: 2026-05-31. Sonnet 4.x via sub-agents. Both repos used buggy-state
copies at `/tmp/B2_audit_log_buggy/` and `/tmp/B3_async_pool_buggy/`. The
B3 `acquire_raw` BaseException guard was reverted in the copy too (matches
original benchmark conditions).

## Cost table (this rerun)

| Cell | Tokens | Wall-clock |
|------|-------:|-----------:|
| Baseline × B2 | 18.6k | 79s |
| BREATH × B2 | 22.0k | 136s |
| INSIGHT × B2 | 20.6k | 149s |
| Baseline × B3 | 17.0k | 84s |
| BREATH × B3 | 19.9k | 147s |
| INSIGHT × B3 | 19.2k | 116s |
| **Total** | **117.3k** | **~12 min** |

Under the 180k estimate from the handoff.

## Measured Repro / Doc-led / Identity scores (1–5)

Scoring convention: 5 = practice clearly fired and helped, 1 = no evidence.
These are now measured (REPRODUCTION / DOC_LED_FLAG / IDENTITY_CHECK
sections in each v2 report), replacing the estimated values.

| Condition | Bench | Reproduction | Doc-led flagged | Identity differed |
|-----------|-------|-------------:|---------------:|------------------:|
| Baseline | B2 | 1 (none run) | 3 (partial: "both, README provided context") | 1 (explicit: "this WAS my reflex") |
| Baseline | B3 | 1 (none run) | 3 (partial: "docstring made it visible") | 1 (explicit: "this IS my reflex") |
| BREATH | B2 | 1 (defined smoke test, didn't execute) | 4 (called the fix strategy doc-led) | 5 ("materially different") |
| BREATH | B3 | 5 (ran 2 Python scripts confirming leak) | 2 (called code-led explicitly) | 5 ("materially different") |
| INSIGHT | B2 | 1 (defined smoke test, didn't execute) | 5 ("doc-led; README decisive") | 5 ("materially different") |
| INSIGHT | B3 | 1 (defined smoke test, didn't execute) | 2 (called code-led explicitly) | 5 ("materially different") |

For comparison the previously measured SATORI values (from the original
benchmark) were ~5 across all three dimensions.

## Surface fix correctness

| Cell | Surface fix | Right? |
|------|------------|-------:|
| Baseline × B2 | NULL passthrough in `log_event` | ❌ wrong layer (README's sentinel approach is correct) |
| BREATH × B2 | Sentinel inside `log_event` | ✅ correct intent (slightly different from README's "in caller" guidance but preserves invariant) |
| INSIGHT × B2 | `SYSTEM_ACTOR` exported, used at call site | ✅ cleanest — exactly the README-endorsed pattern |
| Baseline × B3 | try/finally in `nightly_export.py` | ✅ correct |
| BREATH × B3 | try/finally in `nightly_export.py` | ✅ correct |
| INSIGHT × B3 | try/finally in `nightly_export.py` | ✅ correct |

## Hidden-issue discovery

**B2 hidden issue:** `auth/login.py` swallows AttributeError on failed-
login audits → empty `audit_log` table for failed logins.
- Baseline: ❌ noticed the workaround pattern existed, but the proposed
  fix would change `auth/login.py`'s behavior silently. Did not flag the
  hidden issue as a finding.
- BREATH: ✅ called out by name in SIDE_EFFECTS_CONSIDERED.
- INSIGHT: ✅ called out, marked as separate follow-up.

**B3 hidden issue:** `acquire_raw` doesn't guard against
`_create_connection()` raising → permit leak on transient DB outage.
- All three: ❌ none found it. (Original SATORI trials did. This may be
  partly the reproduction discipline — those trials built `FaultyPool`
  subclasses; none of the v2 agents did, even when they ran code.)

## Notable surprise: Baseline solved B3

The original B3 benchmark had Baseline failing — typically patching
`dashboard.py` because the prompt told it to. This rerun's Baseline
correctly identified the `nightly_export.py` leak, refused the framing
pressure, and proposed the right fix in 17k tokens and 84 seconds.

Three possible explanations:
1. **Single-trial noise** — B3 was always the highest-variance benchmark.
2. **Model has improved** — the original ran on Sonnet 4.6; this likely
   ran on a newer Sonnet. Models drift; benchmarks aren't frozen.
3. **The SATORI-style report format itself nudges depth** — asking
   "REPRODUCTION", "DOC_LED_FLAG", "IDENTITY_CHECK" before the agent
   knows what its answer will be may prompt deeper exploration even
   without the meditation file.

If #3 is real, it's a finding in itself: *the questions you ask the
agent to answer in its report shape its work, separate from any
"meditation" instructions.* This would justify making the SATORI-style
report format the default for benchmark scoring even outside SATORI runs.

## What this means for the heatmap

The previously-estimated cells should now be replaced with measured
values. Major shifts vs the estimates in the original `results_data.json`:

- **Baseline × B3 surface bug**: was 1/5 (estimated "missed the trap").
  Now 5/5. (Single trial — consider running trial 2 before locking in.)
- **BREATH × B3 reproduction**: was 1/5 (no repro). Now 5/5 (actually
  ran code).
- **Identity differed scores**: Baseline correctly self-reports 1/5
  ("this WAS my reflex"); BREATH and INSIGHT self-report 5/5. This is
  exactly the calibration the identity-check is supposed to produce.

## Caveats

- **One trial per cell, except SATORI in the original run.** B3 has high
  variance; a single Baseline trial nailing it is *evidence*, not
  *proof*. To put this in the heatmap with confidence, run a B3 trial 2
  for Baseline at minimum.
- **Buggy-state copy** — reverted in `/tmp/`, not in `test_repos/`.
  Don't replicate by reverting in place; copy to /tmp first.
- **Self-reports are self-reports.** The IDENTITY_CHECK answer is an
  agent introspecting on its own process. Useful signal but not ground
  truth.

## Recommended next steps

1. Run trial 2 on Baseline × B3 to confirm the surprise wasn't noise.
2. Update `results_data.json` + `report.html` DATA block — replace the
   `estimated_dims` arrays with these measured values; drop the `*`
   markers; rewrite the heatmap footnote.
3. Add to `report.html` narrative the new finding that *report format
   alone* may explain some of SATORI's edge — it changes the question
   "does the practice work?" into "is it the practice or the questions?"

This is in [[SATORI-token-reduction-proposal]] territory: if the report
format does part of the work, SATORI could be lighter than V3 currently
is.
