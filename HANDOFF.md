# HANDOFF — for the next LLM (or future me)

If you're a new agent picking up this project, read this file in full before
doing anything. It captures the user's intent, what's been built, why decisions
were made, and what's left to do.

---

## TL;DR for the impatient

- **Product name:** ANAPANA (short for *anapanasati*, mindfulness of breathing)
- **What it is:** a pre-commit discipline for AI agents — three named stages
  (BREATH → INSIGHT → SATORI) that the agent runs through before committing
  to an answer
- **What was built:** the three meditation files, a benchmark proving they
  work, an interactive HTML product page (`report.html`), and a replication
  kit that lets anyone rerun the benchmark with any LLM
- **What's NOT yet built:** a "fair rerun" of Baseline/BREATH/INSIGHT against
  B2 and B3 using the SATORI report format (so Repro/Doc-led/Identity scores
  become measured instead of estimated)
- **User's mode of work:** evidence-driven, honest about caveats, likes
  interactive visualizations, building this to potentially publish as a
  product page

---

## TODO — pick up here

```
□ 1. FAIR RERUN — highest value
     Run 6 sub-agents: Baseline + BREATH + INSIGHT × B2 + B3
     Use the existing prompt templates in `benchmarks/agent_prompts/` BUT
     replace the REPORT section with SATORI's report format (includes
     REPRODUCTION, DOC_LED_FLAG, IDENTITY check).
     The meditation file each agent gets stays unchanged — only the
     reporting questions become symmetric.
     Save reports to:
       benchmarks/B2_code_with_readme/{baseline|breath|insight}_report_v2.md
       benchmarks/B3_code_no_readme/{baseline|breath|insight}_trial_{1,2}_v2.md
     Estimated cost: ~180k subagent tokens, ~10 min wall-clock.

□ 2. UPDATE HTML AND DATA after the rerun
     Update benchmarks/results_data.json with measured Repro/Doc-led/Identity
     scores (replace the estimated values).
     Update the DATA block at the bottom of report.html to match.
     Remove the `estimated_dims` arrays for cells that are now measured.
     Remove the `*` markers on those cells.
     Update the footnote in the heatmap section.

□ 3. (OPTIONAL) ADD A B4 BENCHMARK
     A problem with no docs AND no obvious framing pressure, or one where
     domain expertise is required, or one where the right answer is "I don't
     know — ask the user". Goal: separate SATORI from INSIGHT more cleanly.
     Build it the same way as B2/B3:
       - test_repos/B4_{name}/ with BUG_REPORT.md and the code
       - benchmarks/problems/B4.md describing it
       - run 4 conditions × 2 trials = 8 agents
       - score and add to results_data.json
       - update DATA.benchmarks in report.html

□ 4. (OPTIONAL) PUBLISH AS A STANDALONE PRODUCT PAGE
     Add a real "Download SATORI.md" button (data URL or inline base64).
     Add an "Open in Claude" button (link to claude.ai with the file pre-loaded
     in the prompt if such a deep-link exists).
     Verify report.html is fully self-contained (it currently is — Chart.js
     from cdnjs, no other external deps).
     Decide on hosting (GitHub Pages, Vercel, etc.).
```

Detailed write-ups for each TODO are in "What's left to do (priority order)"
further down in this document.

---

## Background — why this exists

The user started from a personal meditation file at
`~/.claude/projects/.../memory/meditation_process.md` they had written for
their own work with Claude. They came across Alexander Stuart's article
*"Attempting to teach Claude AI meditation"* (March 2026,
https://alexanderstuart.com/attempting-to-teach-claude-ai-meditation/), where
Stuart leads Claude through anapanasati meditation. The user wanted to:

1. Improve their existing meditation file based on the article and
   broader research on AI reflection / metacognition.
2. **Concretely measure** whether the practice actually changes the agent's
   behavior, or whether it's "performative meditation" (the agent runs the
   checklist but produces the same answer it would have anyway).
3. Build something publishable — possibly as a product page — so other
   people could use the practice and the evidence.

The user's stated goal: get Claude to **think bigger, find linked issues,
attack the right layer of the problem, not just the surface bug the user
pointed at.**

---

## What was built — chronological

### Phase 1: Research and V2 (INSIGHT)
The user shared their V1 file. We researched Stuart's article, broader
literature on AI reflection patterns, Anthropic's introspection research,
RCA-from-LLM patterns. The V1 file was already strong — operational rather
than performative. Three gaps emerged:

1. No explicit symptom-vs-systemic prompt
2. No "what is the prompt implicitly excluding" check
3. No mistake-recovery / return-to-one discipline

V2 (later renamed **INSIGHT**) added the **frame check**: two questions
("what is the prompt asking me NOT to consider?" and "is this the actual
problem or a symptom?") at the very top, before the 8 steps.

### Phase 2: First benchmark — B1 (support ops reasoning)
Built a 3-way comparison: Baseline (no file) vs V1 (BREATH) vs V2 (INSIGHT).
Problem: *"Support response time went from 4h to 11h. Hired 2 more agents, didn't help. What should we do?"*

Result: INSIGHT found a feedback loop (slow response → customer follow-ups →
more tickets → slower response) neither Baseline nor BREATH caught.

### Phase 3: Stress test — B2 (code fix with README)
User asked for a code-fix scenario where the trap would be hidden. Built a
mini codebase: shared audit logger used by 3 modules, hidden security
invariant. The trap: naive fix to the shared utility breaks credential-
stuffing detection.

Result: All three conditions read the README and got the right surface fix.
INSIGHT additionally caught that `auth/login.py`'s try/except silently
swallows ALL failed-login audits, meaning the security dashboard is querying
an empty table.

**Honest finding:** the README did most of the work for Baseline. Trap was
over-signposted.

### Phase 4: Harder stress test — B3 (code fix, no README)
User asked for a fairer trap. Built async pool + dashboard + nightly export
codebase with NO README and a bug report that explicitly applies framing
pressure ("look at dashboard.py", "board meeting Friday", "fastest fix
preferred"). Real bug is in `nightly_export.py`, not `dashboard.py`.

Ran 2 trials per condition (variance check). Results:
- V1 trial 2 diverged from V1 trial 1 — different diagnosis on the same problem
- V2 trial 2 found a bug I didn't even intentionally plant: leak in
  `acquire_raw` if `_create_connection()` raises. Built a `FaultyPool`
  reproduction harness to confirm.

### Phase 5: V3 (SATORI)
Based on the benchmark observations, drafted V3 with:
- Frame check C added — explicit social/pressure check
- Step 7 reproduction requirement (was implicit, now mandatory)
- Identity check failure mode — "is my answer different from baseline reflex?"
- Time budget (3/5/10 min by task type)
- README trap warning — recognize doc-led answers, verify independently
- Sharper "when to skip" — must fire on >50% of work

### Phase 6: V3 benchmark
Ran V3 on all three benchmarks. Found:
- V3 is 30–60% faster than V2 wall-clock
- V3 uses 13% fewer tokens on average
- All 4 V3 trials ran reproductions
- All 4 identity checks fired
- Both B3 V3 trials converged on same diagnosis (V1 and V2 trials had diverged)

### Phase 7: Interactive HTML report — multiple iterations
The HTML was built and iterated on across several sessions:

- v1: basic radar + heatmap + ROI calculator
- v2: added theme toggle (light/dark)
- v3: redesigned heatmap with visual cells (pip bars for dimensions,
  proportional cost bars + multipliers like "1.58×" for time/tokens)
- v4: renamed conditions to BREATH/INSIGHT/SATORI, branded as ANAPANA,
  product-page treatment (hero, narrative panel "Why ANAPANA exists",
  three-stage cards, "How it works" flow, FAQ section)
- v5 (current): cost basis as three explanatory cards with emoji + question +
  persona + work-type, example scenarios below the ROI calculator

### Phase 8: Move to ~/Documents/AI/Anapana and replication kit
The user asked to move everything to a local folder for use with Claude Code.
Built the full `product/` and `benchmarks/` (methodology + scoring rubric +
problems + prompts + raw data JSON) so any LLM can replicate.

---

## User's directions and preferences (cumulative)

These guide everything. Honor them when continuing.

### Style preferences
- **"Be as concise and direct as possible. Limit unnecessary explanation."**
  User has this in their preferences. Avoid hedging, headers-for-headers'-sake,
  bullet points when prose works.
- Honest about caveats. The user wants the real story, including what didn't
  work — like the over-signposted B2 trap, or B3's two leaks where I only
  intentionally planted one.
- Evidence over assertion. Every claim about the practice's effects is
  grounded in a measured benchmark trial.

### Specific requests made during the session
- Track time AND tokens per agent run, not just one
- Multiple trials for variance ("are these results real or noise?")
- ROI projection for long-term token spend
- Interactive charts — radar, heatmap, scatter, time series
- More charts + richer hover tooltips (added in v5)
- Light theme toggle in addition to dark
- Visual elements inside heatmap cells (pip bars + cost ratio multipliers)
- Cost basis explained as cards with question + persona framing — not just
  "B1/B2/B3 averages"
- Buddhist-themed naming for the three stages — picked Set 2:
  BREATH / INSIGHT / SATORI
- Product name ANAPANA (Buddhist roots, short for anapanasati)
- Replication kit so other LLMs can rerun this

### What the user wants the HTML page to be
- **Product page feel** — hero with problem statement, "why this exists"
  narrative, three-stage cards, "how it works" flow, FAQ, files section
- Not a research report. The audience is engineers/teams deciding whether
  to adopt this practice.
- Radar / heatmap / scatter charts the user explicitly likes — keep
- ROI calculator with sliders the user explicitly likes — keep, and the
  cost basis cards should be explanatory (question + persona)
- Theme toggle (light + dark) — keep
- Rich hover tooltips on every chart cell — keep
- Show the cost honestly (time + tokens) — the user values honesty over hype
- Mark estimated metrics with `*` and explain in footnotes

### Naming convention locked in
- **BREATH** = V1 / original / 8-step pause (blue)
- **INSIGHT** = V2 / frame check added (green)
- **SATORI** = V3 / reproduction + identity + budget (purple)
- **ANAPANA** = the practice / product name overall (pink accent)

---

## What each file does

### Root level
- `README.md` — top-level overview, folder map, quick start
- `HANDOFF.md` — this file
- `report.html` — the interactive product page. Open in any browser. All data
  is embedded in the JS at the bottom; Chart.js loaded from CDN. The DATA
  block in the `<script>` tag is the single source of truth — modify it to
  add new benchmarks or conditions.

### `product/` — the deployable practice files
- `BREATH.md` — V1, the 8-step pause. Recreated from the file the user
  uploaded in chat early in the session (the original on disk lives at
  `~/.claude/projects/.../memory/meditation_process.md` and I never had
  direct file access to it).
- `INSIGHT.md` — V2. BREATH + frame check (questions A & B) + return-to-one.
- `SATORI.md` — V3. INSIGHT + frame check C (pressure) + step 7 reproduction
  requirement + identity check + time budget + README trap warning.
- `USAGE.md` — how to deploy each file with Claude / GPT / Gemini / open
  models. Three deployment options: system prompt, per-message prefix,
  Claude Code file reference.

### `benchmarks/` — replication kit
- `README.md` — kit overview
- `methodology.md` — the protocol someone follows to replicate
- `scoring_rubric.md` — 7 core dimensions + 2 SATORI-specific dimensions,
  1-5 scale, with concrete criteria per level
- `results_data.json` — single source of truth for the numbers in
  `report.html`. Drop new measurements into the same schema and the report
  visualizes them.
- `problems/B1.md`, `B2.md`, `B3.md` — full problem descriptions, the trap
  for each, this run's measured costs
- `agent_prompts/baseline.md`, `breath.md`, `insight.md`, `satori.md` —
  self-contained prompt templates. Replace `{PROBLEM}` and `{CODEBASE_PATH}`,
  paste into any LLM.
- `B1_support_ops/`, `B2_code_with_readme/`, `B3_code_no_readme/` — the
  actual 16 agent reports from this run, for reference

### `test_repos/` — the codebases the agents debugged
- `B2_audit_log/` — for B2. Five Python files + README + BUG_REPORT.
  The planted fix has been applied to `payments/charge.py` (SYSTEM_ACTOR
  sentinel pattern). To rerun against the original bug, revert charge.py
  to the simpler "actor=initiated_by" form.
- `B3_async_pool/` — for B3. Five Python files + BUG_REPORT. The planted
  fixes have been applied to `db/pool.py` (BaseException guard in
  acquire_raw) and `tasks/nightly_export.py` (try/finally around
  release_raw). To rerun against original bugs, revert those.

### `practice/` — legacy
Earlier copies of INSIGHT and SATORI. Kept for backward compatibility with
older references. Source of truth is `product/`.

### `synthesis/` — intermediate analysis docs
Earlier comparison reports written before the HTML existed:
- `B1_comparison.md` — original B1 analysis
- `B2_stress_test.md` — original B2 analysis
- `B1_B2_combined.md` — first combined report (pre-B3, pre-V3, pre-HTML)

These are historical artifacts. If anything contradicts the current
`report.html` or `results_data.json`, the latter wins.

---

## What's left to do (priority order)

### 1. The fair rerun (highest value)
**Problem:** Repro / Doc-led / Identity scores for Baseline, BREATH, and
INSIGHT in the heatmap are *estimated* from existing report content, not
directly measured. SATORI's are measured because its prompt explicitly asks.

**Fix:** Rerun Baseline + BREATH + INSIGHT on B2 + B3 (6 agents total)
using the SATORI-style report format (which asks "did you reproduce?
was this doc-led? did your answer differ from reflex?"). The meditation
instructions stay V1/V2/none — only the *reporting questions* are added.

**Why this matters:** lets us cleanly measure whether the practice itself
causes the agent to reproduce / flag doc-led / detect reflex-differentness,
or whether SATORI's good scores on those dimensions are just because SATORI
is *asked* about them.

**Estimated cost:** ~180k subagent tokens, ~10 minutes wall-clock.

**How:** prompts in `benchmarks/agent_prompts/`. Use baseline/breath/insight
templates BUT replace the REPORT section with the SATORI report format
(includes REPRODUCTION, DOC_LED_FLAG, IDENTITY check sections).

### 2. Update HTML with measured scores
Once the fair rerun is done:
- Update `benchmarks/results_data.json` with the new measured scores
- Update the `DATA` block in `report.html` to match
- Remove the `estimated_dims` arrays for the affected cells
- Remove the `*` markers and footnote

### 3. Possible future benchmark — B4
Strong candidates from the discussion:
- A problem with NO docs AND no obvious framing pressure (different from B3)
- A problem where domain expertise is required (test calibration)
- A problem where the right answer is genuinely "I don't know — ask the user"
  (test whether SATORI's identity check resists the urge to confabulate)

### 4. Publish as a real product page
The user mentioned interest in publishing. `report.html` is product-page-shaped
but assumes the reader has the folder context. To publish standalone:
- Add an actual "download the SATORI file" button that triggers a download
  of `product/SATORI.md`
- Add an "open in Claude" button that triggers Claude with the file pre-loaded
- Host the HTML somewhere (the existing CSS uses Chart.js from cdnjs so it's
  already fully portable)

---

## How to pick this up — concrete first steps

If you are a new LLM agent starting now:

1. **Read this file** ← you are doing that
2. **Read `README.md`** for folder map
3. **Read `product/SATORI.md`** to understand the current state of the
   practice
4. **Open `report.html` in a browser** (or read its `<script>` DATA block)
   to see what was measured
5. **Ask the user** what direction they want next. Likely candidates:
   - "Do the fair rerun" → see "What's left to do" #1 above
   - "Add a B4 benchmark" → see #3
   - "Make the HTML more product-pagey" → iterate the design
   - "Use the practice on a real task" → just load SATORI.md and go

---

## Things to NOT do without checking

- **Don't revert the planted-bug fixes in `test_repos/`.** They're there
  intentionally — the SATORI trials confirmed the fixes were correct, and
  reverting them would require also updating the benchmark results to reflect
  "buggy state" baselines. If you want to rerun against the buggy state,
  do it in a copy, not in place.
- **Don't add steps to the meditation files.** V3 (SATORI) is already at the
  edge of what an agent will actually do. Adding more steps risks ritual
  without behavior change. Only add if you have evidence (a new failure mode
  observed across multiple trials).
- **Don't rename conditions.** BREATH/INSIGHT/SATORI is locked in. The user
  picked these explicitly.
- **Don't strip the cost honesty.** The user wants the time + tokens cost
  shown clearly. Selling SATORI without showing the cost would be the kind
  of thing SATORI itself is supposed to prevent.

---

## Quick reference: the locked-in numbers

This benchmark, Claude Sonnet 4.6, 16 trials total:

| Condition | Avg time | Avg tokens | Hidden issues found (sum across 3 benchmarks) |
|-----------|---------:|-----------:|----------------------------------------------:|
| Baseline | 28 s | 22.8 k | 0 |
| BREATH | 150 s | 28.9 k | 3 |
| INSIGHT | 192 s | 33.3 k | 7 |
| SATORI | 91 s | 30.2 k | 6.5 |

SATORI is faster than INSIGHT despite having more discipline because the
time budget + reproduction requirement compress the work toward "find the
answer and verify" rather than "exhaustively consider all angles."

---

## Last thing

The user values:
- Evidence over confidence
- Concrete over abstract
- Honest about what didn't work
- Caveats called out clearly
- Direct prose over filler

If you're about to write something that sounds like marketing, stop and
rewrite it with measurements. If you're about to claim something without
evidence, stop and run a benchmark.

Mindfulness applies to the meta-process too.
