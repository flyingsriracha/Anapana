# ANAPANA

A pre-commit discipline for AI agents. Pause. Reframe. Reproduce. Then act.

This folder contains everything we built across the session: the practice files
ready to deploy with any LLM, the full replication kit (problems, prompts,
scoring rubric, raw data), the benchmark evidence (16 agent trials across 3
problems), the test codebases, and the interactive report.

---

## Quick start

1. **To use the practice with Claude / GPT / Gemini / any LLM:** open
   `product/USAGE.md`. Pick the file (`BREATH.md`, `INSIGHT.md`, or
   `SATORI.md`) — paste it as a system prompt or prefix.
2. **To view the evidence:** open `report.html` in any browser. Interactive
   charts, heatmap, ROI calculator, theme toggle.
3. **To replicate the benchmarks with your own model:** open
   `benchmarks/README.md`. Has the methodology, prompts, scoring rubric,
   and raw data.

---

## Folder layout

```
Anapana/
├── README.md                        ← you are here
├── HANDOFF.md                       ← READ THIS FIRST if you are a new LLM picking up the project
├── report.html                      ← interactive product page
│
├── product/                         ← THE DEPLOYABLE PRACTICE FILES
│   ├── BREATH.md                    Stage 01 — 8-step pause
│   ├── INSIGHT.md                   Stage 02 — BREATH + frame check
│   ├── SATORI.md                    Stage 03 — INSIGHT + repro + identity (RECOMMENDED)
│   └── USAGE.md                     how to deploy with any LLM
│
├── benchmarks/                      ← REPLICATION KIT
│   ├── README.md                    overview
│   ├── methodology.md               full protocol
│   ├── scoring_rubric.md            7+2 dimensions, 1-5 scale
│   ├── results_data.json            raw numbers behind the charts
│   ├── problems/                    the three benchmark problems
│   │   ├── B1.md                    support ops reasoning
│   │   ├── B2.md                    code fix w/ README
│   │   └── B3.md                    code fix no README (the trap)
│   ├── agent_prompts/               4 self-contained templates
│   │   ├── baseline.md              no meditation
│   │   ├── breath.md                with BREATH inlined
│   │   ├── insight.md               with INSIGHT inlined
│   │   └── satori.md                with SATORI inlined
│   ├── B1_support_ops/              actual agent reports from this run
│   ├── B2_code_with_readme/         "
│   └── B3_code_no_readme/           " (2 trials per condition)
│
├── test_repos/                      ← codebases for B2 and B3
│   ├── B2_audit_log/                shared logger + 3 consumers + README
│   └── B3_async_pool/               async pool + dashboard + nightly export
│
├── practice/                        ← (legacy — same as product/, kept for backward refs)
│   ├── INSIGHT_meditation_process.md
│   └── SATORI_meditation_process.md
│
└── synthesis/                       ← intermediate analysis docs
    ├── B1_comparison.md
    ├── B2_stress_test.md
    └── B1_B2_combined.md
```

---

## The three stages

| Stage | Adds | When to invoke |
|-------|------|----------------|
| **BREATH** | The 8-step checklist | Any non-trivial decision |
| **INSIGHT** | + Frame check ("what's excluded?") | Prompts that feel narrow or pressured |
| **SATORI** | + Reproduction, identity check, time budget | High-stakes / hidden-dependency / multi-file work |

Each stage subsumes the previous. **Use SATORI** unless you have a specific
reason to fall back to a simpler one.

---

## What the benchmarks showed

- **SATORI is on a new Pareto frontier.** Maintains INSIGHT's quality but is
  30–60% faster and uses 13% fewer tokens on average.
- **All 4 SATORI trials ran reproductions.** B1: traced hypothesis arithmetic.
  B2/B3: executed Python.
- **All 4 identity checks fired.** Each SATORI agent explicitly named how its
  answer differed from baseline reflex.
- **SATORI trials converged** on B3 where BREATH and INSIGHT trials diverged.
  Lower variance = single runs are more trustworthy.
- **Baseline is more capable than expected** when docs are explicit. B2 and B3
  both had docs that taught Baseline the right answer.

See `report.html` for the full breakdown with charts.

---

## To replicate with another LLM

The complete replication kit is in `benchmarks/`. Walking through it:

1. Read `benchmarks/methodology.md` — overall protocol, ~5 min read.
2. Pick a benchmark (B1, B2, B3) from `benchmarks/problems/`.
3. For each condition you want to test, copy the matching template from
   `benchmarks/agent_prompts/` — replace `{PROBLEM}` with the problem text and
   `{CODEBASE_PATH}` with the path to the test repo (for code tasks).
4. Run the agent. Score its report using `benchmarks/scoring_rubric.md`.
5. Compare your numbers to `benchmarks/results_data.json` (this run's numbers
   from Claude Sonnet 4.6).

To compare against this run's actual agent reports for reference, look in
`benchmarks/B{1,2,3}_*/` — those are the full markdown reports each Claude
sub-agent produced.

---

## Status of the data

- **Measured directly:** time, tokens, tool uses, surface-bug correctness,
  bigger-picture awareness, considered-consumers, preserved-invariants,
  resisted-grasping, confidence calibration, hidden-issues found.
- **Estimated from report content** (not directly measured for non-SATORI
  conditions): the Repro / Doc-led / Identity scores. Cells with a `*` in
  the heatmap. A fair rerun should ask Baseline / BREATH / INSIGHT agents
  the same questions so the comparison is fully apples-to-apples. The
  `benchmarks/agent_prompts/` templates already support this if you run them
  yourself.

---

## Housekeeping

`__pycache__/`, `.pytest_cache/`, and `.DS_Store` files inside `test_repos/`
are leftover Python and macOS artifacts. Harmless — delete via Finder or:

```bash
find ~/Documents/AI/Anapana -name __pycache__ -type d -exec rm -rf {} +
find ~/Documents/AI/Anapana -name .pytest_cache -type d -exec rm -rf {} +
find ~/Documents/AI/Anapana -name .DS_Store -delete
```

---

## Origin

This practice was inspired by Alexander Stuart's article *"Attempting to teach
Claude AI meditation"* (March 2026), where he tried to lead Claude through
anapanasati — mindfulness of breathing. The conversation surfaced a useful
parallel: the pull toward "completing the sentence" that meditation tries to
loosen in humans is also what AI agents do — they always reach for the
resolved answer. The same antidote applies. Notice the pull. Don't obey it.

The name **ANAPANA** is shortened from *anapanasati* — the practice itself.
