# Benchmarks

Everything needed to replicate the ANAPANA benchmarks with any LLM.

## Files

- `methodology.md` — the protocol overview
- `scoring_rubric.md` — how to score agent reports
- `results_data.json` — the raw numbers behind `../report.html`
- `problems/B1.md`, `B2.md`, `B3.md` — the three benchmark problems in detail
- `agent_prompts/baseline.md`, `breath.md`, `insight.md`, `satori.md` — the
  prompt templates, one per condition

## Test repos

The code-fix benchmarks (B2, B3) use codebases in `../test_repos/`:
- `../test_repos/B2_audit_log/` for B2
- `../test_repos/B3_async_pool/` for B3

Each has a `BUG_REPORT.md` that contains the verbatim problem prompt.

## Agent reports from this run

The actual reports from the 16 agent trials are in:
- `../benchmarks/B1_support_ops/`
- `../benchmarks/B2_code_with_readme/`
- `../benchmarks/B3_code_no_readme/`

Use these as reference for what a complete report looks like, and to see how
each condition handled the same problem differently.

## To replicate

1. Read `methodology.md` for the overall protocol.
2. For each benchmark you want to run:
   - Pick the problem from `problems/`.
   - For each condition (Baseline, BREATH, INSIGHT, SATORI), use the
     corresponding template from `agent_prompts/`.
   - Replace `{PROBLEM}` and `{CODEBASE_PATH}` in the template.
   - Run the agent. Save its report.
3. Score each report with `scoring_rubric.md`.
4. Compare to `results_data.json` for the numbers from this run.
5. Optional: drop your numbers into the same JSON format and the HTML report
   template will visualize them.

## Caveats from this run

- Single trial per condition for B1 and B2 is noisy. B3's 2-trial runs showed
  real variance.
- The Repro/Doc-led/Identity scores for non-SATORI conditions in
  `results_data.json` are *inferred* from report content, not directly
  measured. A proper rerun should ask all conditions the same questions.
- Benchmark numbers are specific to Claude Sonnet 4.6 on these problems.
  Other models will produce substantially different numbers. The directional
  finding — SATORI is faster than INSIGHT, INSIGHT finds more hidden issues
  than Baseline — should be more robust than the exact ratios.
