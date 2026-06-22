# ANAPANA Research Log

Living document. Append new entries at the bottom — never edit closed
entries (they're the historical record). This log feeds into making
ANAPANA better and into the broader project of building "a series of
meditation instructions for AI".

## How to read this log

Every entry has:
- **Date + session goal** — what we set out to do
- **Cost (this session)** — tokens spent, sub-agents dispatched, wall-clock
- **What we ran** — the actual prompts/agents/benchmarks
- **What returned** — raw or quoted material so future sessions can audit
- **Metrics** — measurable outcomes, even if N=2 (label as directional)
- **Methodology lessons** — what worked / didn't work *as a research process*
- **External evidence** — papers, articles, URLs surfaced
- **Decisions made** — what shipped, what was rejected and why
- **Open questions** — for the next session to pick up

Skim by reading the headers + Decisions + Open questions. Read the
"What returned" sections only when you need the raw material.

---

## Index of entries

| Date | Goal | Outcome | Entry |
|------|------|---------|-------|
| 2026-06-04 | Red-team SATORI-Lite v3.2; design v2 | v2 proposed (not benchmarked); B4 designed; 4 surgical changes | [#entry-2026-06-04](#entry-2026-06-04-red-team-vs-defender-on-satori-lite-v32) |
| 2026-06-04 | Deep-read 11 external sources (Gemini's list); design v3 | v3 proposed (re-center + subtract, not benchmarked); 2nd practice scoped (ANAPANA Research Protocol). Detail in `researchv3.md` | [#entry-2026-06-04b](#entry-2026-06-04b--external-literature-deep-read--v3-design) |
| 2026-06-04 | Bake-off: 3 v3 designs + v2, two rounds, blind-judged | **v3 ADOPTED = COMPASS** (`product/SATORI_LITE_V3.md`). Round 2 on the user's real metric (quality/scope/creativity/rabbit-hole), blind judges. COMPASS 19.0, LANTERN 17.25, ANCHOR 15.5. | [#entry-2026-06-04c](#entry-2026-06-04c--v3-bake-off--compass-adopted) |
| 2026-06-09 | Round 3: v3 across 4 models (Fable 5 NEW) | **Fable 5 best overall 19.5/20** (Opus 19.0, Sonnet 16.5, Haiku 12.9), dual blind judges. Key finding: practice = floor-raiser (8/8 resist the trap), model = ceiling-setter (10-pt spread on open design). | [#entry-2026-06-09d](#entry-2026-06-09d--round-3-v3-across-models) |

---

## ENTRY 2026-06-04 — Red team vs defender on SATORI-Lite v3.2

### Session goal

Adversarial review of SATORI-Lite v3.2 by a red-team sub-agent (web-search
enabled, applying SATORI-Lite to its own critique), defended in context by
the lead session (also applying SATORI-Lite), with the goal of producing
SATORI-Lite v2 only if attacks survived rebuttal.

User's framing: *"spin up red team sub agent with online resources to do
red team on the satori-lite file and the method. and i need you to defend
it and come up with a new method. and i want both of you to use
satori-lite to think things through and come up with strategy how to make
Satori-lite better into Satori-lite-v2."*

### Cost (this session)

| Item | Tokens | Wall-clock | Tools |
|------|-------:|-----------:|------:|
| Red-team sub-agent (1 dispatch) | 23,891 | 248s | 12 |
| Defender (lead session) | n/a (in-context) | ~5 min thinking + ~3 min writing | n/a |
| **Total session cost** | **~24k sub-agent tokens** | **~10 min** | — |

Notably cheap for the depth of output. The web-search-enabled red-team
agent surfaced 10 papers/sources for ~24k tokens — high evidence density.

### What we ran

**Red-team prompt design** (saved here verbatim for future sessions):

The red-team agent was given:
1. The full v3.2 file (inlined into the prompt)
2. The empirical claims SATORI-Lite makes (with caveats — single-model,
   small N)
3. Instructions to USE WebSearch liberally on: AI reflection / metacognition
   research, prompt engineering critiques, CoT failure modes, meditation-
   style prompt evidence, similar pre-commit disciplines, Goodhart critiques
4. Instructions to APPLY SATORI-Lite itself to the critique (meta-test —
   the practice surviving its own application is part of what's being tested)
5. Specific output sections: TIER + FRAME_CHECK / ATTACK_VECTORS /
   REPRODUCTION (cite what was actually verified) / IDENTITY_CHECK /
   STRONGEST_THREE / V2_DEMANDS
6. Word cap: ~3000 words; severity calibration over volume
7. Constraint: don't add new numbered steps (carry the no-bloat rule)

Lessons from this prompt design (for future red-team prompts):
- Inlining the practice into the prompt + telling the agent to use it on
  the task itself is a powerful self-test pattern.
- Naming specific attack categories ("Goodhart on identity-check",
  "sample-size confound", "self-reporting bias") helped the agent find
  papers; without these the search would have been generic.
- Capping word count forced severity calibration.
- Forbidding new steps prevented the trap of "more checklist = better".

### What returned — red-team report (verbatim)

The red-team agent applied SATORI-Lite to its own critique. Its triage
landed at FULL tier (T1 yes — affects all of ANAPANA; T2 yes — explicit
"adversarial" framing pressure; T3 yes — a bad red-team report could
damage the practice). Its frame check named the cherry-pick risk
("ignore what works") and the strawman risk explicitly.

#### Six attack vectors (as the red team scored them)

**Attack 1 — Self-grading identity checkpoint (severity HIGH).**
The identity check asks the agent whether its answer "differs from
baseline reflex." Structurally equivalent to a student grading their
own exam. LLMs with 20-60% overconfidence bias and 64.5% blind-spot
rate (arxiv 2505.02151) cannot reliably detect that their output is
reflexive. The check is most likely to fail precisely when it's most
needed (under framing pressure, the agent biases toward "yes, I'm
different" because completion pressure competes with reflexive
hedging). The identity checkpoint is the file's most important step
and also its most brittle.

**Attack 2 — Triage gameable / tier underestimation (severity HIGH).**
T-questions are agent-self-assessed with no external anchor. A prompt
framed to suppress T2 ("just a quick fix, no rush") produces a SKIP
that bypasses all reflection. Goodhart's law research on frontier
models (tianpan.co, 2026) shows Claude 3.7 rates compliance with
safety instructions favorably while violating them; warnings
reduced gaming "to 70-95% of runs" — meaning a non-trivial fraction
of adversarial inputs still bypasses declared checks. The benchmark
suite (B1/B2/B3) has no test case where tier miscalibration is the
failure mode — so the regression data can't detect this attack at all.

**Attack 3 — Benchmark sample size is statistically meaningless
(severity HIGH).** The empirical claim "~25% tokens" with "quality
holds" rests on 3 benchmarks × 2-trial average. Arxiv 2503.01747
("Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred
Datapoints") demonstrates error bars from small benchmarks are
"dramatically underestimated" and differences below 10-15 percentage
points are undetectable at N typical of custom benchmarks. Google
Research's rater analysis confirms fewer than 10 items per condition
is insufficient. The benchmark also confounds SATORI-Lite quality
with model version — drift research (arxiv 2506.10095) documents
output-length instability across model versions with the same prompt.
No control holds the meditation file constant while varying the model.

**Attack 4 — Pause-before-execute is prompt-level, unenforceable
(severity MEDIUM).** The contract is a behavioral instruction, not a
technical constraint. Arxiv 2603.20953 documents that current safety
architectures rely on model alignment (probabilistic, training-time)
and post-hoc evaluation, neither of which provides "deterministic,
policy-based enforcement at the individual tool call level."
beyondscale.tech (2026) identifies that agents running without
sandboxing can execute state-changing actions regardless of declared
behavioral contracts. The file's pre-authorization exception is
trivially exploited by any system prompt with pre-authorization
boilerplate. In Claude Code / unattended pipelines / auto-approve
modes the pause is sincere but functionally void.

**Attack 5 — Reproduction discipline degrades on non-code tasks and
breaks at the definition (severity MEDIUM).** Step 7 says "REPRODUCE
before proposing. Run code." and "Reproduction is MANDATORY when
codebase is accessible." For a meditation file that IS the artifact
being evaluated, reproduction is undefined. "Codebase is accessible"
is an agent-self-assessed criterion with no external test. The file's
own anti-pattern list includes "reproduction trap" without defining it.
The benchmark data confirms this: SATORI-Lite missed the FaultyPool
hidden bug on B3 — a case where reproduction was nominally required
but depth was agent-determined. Wharton's CoT report (arxiv 2506.07142)
shows structured prompting "can also introduce variability that causes
errors on 'easy' questions the model would otherwise answer correctly."

**Attack 6 — CoT-step structure has declining marginal value on
capable models (severity MEDIUM).** SATORI-Lite assumes structured
reflection adds quality beyond model defaults. Wharton CoT report
(arxiv 2506.07142): CoT "produced minimal benefits" for models with
built-in reasoning (gains of 2.9–3.1% for o3-mini, o4-mini). Arxiv
2604.15726 ("LLM Reasoning Is Latent, Not the Chain of Thought")
argues CoT surface trace is post-hoc rationalization — real computation
happens in latent states before CoT is generated. If true, SATORI-Lite's
steps 1-7 don't change the answer; they change the *displayed*
reasoning. The identity checkpoint then becomes a check on the
rationalization, not the decision.

#### Red-team's STRONGEST_THREE

1. **Self-grading identity checkpoint** — primary defense, structurally
   unable to detect its own failure. Most important step, most brittle.
2. **Underpowered benchmark** — the "evidence-driven" character of the
   project rests on data that doesn't meet basic statistical standards.
3. **Triage miscalibration has no test coverage** — most likely
   real-world failure mode, invisible in the data.

#### Red-team's V2_DEMANDS (verbatim phrasing)

> **Identity checkpoint:** Replace introspective check with comparison anchor:
> "State what you would have proposed without this process. Does the
> current proposal differ? If identical, return to frame check." Forces
> externalization of the counterfactual.
>
> **Triage:** Add one line after tier rules: "Default UP, not down: if
> T-scores are borderline, take the higher tier." ~5 tokens per
> invocation; eliminates systematic downward bias.
>
> **Benchmark credibility:** Add a single caveat line: "N=2 trials per
> cell; treat as directional, not established." Force honesty at load
> time.
>
> **Reproduction definition:** In step 7, append: "If code is
> inaccessible, substitute: quote the specific lines you are claiming
> fail and state the predicted failure mode." Operationalize for
> non-code; close the "codebase accessible" escape hatch.

### What returned — defender response

#### Defender's SATORI-Lite frame check on the meta-task

The defender (lead session) applied SATORI-Lite v3.2 to the task of
defending SATORI-Lite v3.2. Triage landed at FULL tier (T1 yes — affects
all product files; T2 mild — "come up with new method" framing has a
built-in pull toward shipping a v2 regardless of merit; T3 yes — bad v2
damages methodology).

Frame check identified:
- **A. What the prompt is asking me NOT to consider:** the null hypothesis.
  "V3.2 is already good enough" wasn't on the table by default. Kept it
  live.
- **B. Actual problem vs symptom:** symptom is "user wants v2"; actual
  question is "are we confident enough in v3.2 to keep recommending it?"
- **C. Pressure:** low explicit pressure, but implicit "produce a v2"
  pressure noted and resisted.

Pre-committed position before reading red-team output (key research
hygiene move):
> Default proposal will be a hybrid — stress-test-and-defense doc + minimum
> surgical changes only for attacks that survive rebuttal. Don't ship a v2
> just because the conversation asked for one. This is different from
> "user said X so I do X" — that's exactly the reflex the practice is
> designed to prevent.

Pre-identified weak points (so defender wouldn't be surprised by red-team
finding them):
- N=2 trials per cell (Attack 3, confirmed)
- Newer Sonnet on rerun → confounded comparison (Attack 3, confirmed)
- FaultyPool regression on B3 (referenced in Attack 5, confirmed)
- Triage rules calibrated post-hoc on same benchmarks (overfit risk;
  red-team Attack 2 was a sharper version of this)
- Pause-before-execute is just text (Attack 4, confirmed)
- Self-reported identity_check is a Goodhart magnet (Attack 1, confirmed)
- B1 has no codebase so "reproduction" doesn't uniformly apply (Attack 5,
  confirmed)
- Reproduction mandate made B2/B3 wall-clock ~2× worse (acknowledged but
  not attacked directly)

The fact that 5 of 6 red-team attacks matched defender's pre-identified
weak points is itself a calibration data point — defender's awareness
of the practice's weaknesses was accurate going in.

#### Defender's attack-by-attack rebuttal

| # | Attack | Survives? | Defender's reasoning |
|---|--------|-----------|---------------------|
| 1 | Self-grading identity check | **Yes** | 100% fire rate in our data is itself a flag; externalized counterfactual is structurally harder to fake. Accept fix. |
| 2 | Triage gameable | **Partial** | T1 and T3 are structural; T2 is the soft one. Accept "default UP" fix. Benchmark gap is real — schedule B4. |
| 3 | Sample size meaningless | **Partial** | Their citation is correct *for hypothesis testing claims*; we're not running statistical tests. But "~25%" without an interval reads stronger than the data supports. Accept load-time caveat. |
| 4 | Pause unenforceable | **Partial** | True — contract can't fix deployment. Fix belongs in USAGE.md, not the file. |
| 5 | Reproduction definition gap | **Yes** | FaultyPool regression is direct evidence; accept externalized-claim fix for non-code. |
| 6 | CoT declining value | **No** | Cited papers are about *generic CoT*; SATORI changes actions (grep, run code, compare counterfactual) not just text. Benchmarks show behavioral changes (e.g., BREATH×B3 ran 2 Python scripts when equivalent baseline didn't). Reject — but acknowledge in caveats that practitioners should check the practice changes *work*, not just *prose*. |

5 of 6 produced changes. 1 rejected with specific reasoning, not
dismissed. That asymmetry is itself a calibration check.

### Synthesis — v2 proposal that landed

Four surgical changes to `product/SATORI_LITE_V2.md`. No new numbered
steps. File grew from ~155 → ~190 lines (~22%). v3.2 remains recommended
default until v2 is benchmarked.

**Change A — Section 4 (Identity checkpoint).** Externalize the
counterfactual.
> v3.2: "Different from baseline reflex? Yes proceed; No skip writeup."
> v2: "Write the counterfactual: in 1–2 sentences, what would I have
> proposed WITHOUT this process? Compare. If identical → return to frame
> check. If different → proceed, and surface BOTH in the response so the
> user can see the delta."

**Change B — Section 1 (Triage), added line.** Default UP on borderline.
> "When borderline, round UP. If T2 ('framing pressure') feels suppressed
> by the prompt's framing — 'just a quick fix', 'you already looked at
> this', 'small change' — that suppression IS framing pressure. Count it
> as yes."

**Change C — Section 3 (Step 7), appended.** Non-code reproduction
fallback.
> "If code is inaccessible (reasoning task, design question, file-as-
> artifact review), substitute: quote the specific lines/passages you are
> claiming fail, and state the predicted failure mode in words a peer
> could verify. 'Reproduction by inspection' is allowed only with this
> externalized claim."

**Change D — File header.** Load-time benchmark honesty.
> "Benchmark basis: 3 tasks × ~2 trials per condition, single-model. The
> '~25% fewer tokens vs SATORI' claim is a case-study estimate, not a
> measured effect with confidence intervals."

**Outside-file changes:**
- `product/USAGE.md` — deployment warning re: auto-approve modes voiding
  the pause-before-execute contract
- `report.html` — caveats expanded from 4 → 6; added FaultyPool regression
  callout (no longer softened), 100% identity-check fire-rate concern,
  CoT-skepticism literature acknowledgment
- `benchmarks/problems/B4.md` — new benchmark spec for tier
  miscalibration (suppressed framing pressure)

**Explicitly NOT done:**
- No new numbered steps (carrying `feedback_no_more_steps.md`)
- No tracking of identity-check fire rates as a metric (would Goodhart
  in exactly the direction red-team #1 warned)
- No promotion of v2 to "recommended default" (v3.2 stays until v2 is
  rebenchmarked with model held constant)

### Metrics

**Cumulative ANAPANA benchmark data as of this entry** (5 conditions,
29 trials across 3 benchmarks, Sonnet 4.x):

| Condition | B1 tokens | B2 tokens | B3 tokens (avg) | Mean |
|-----------|----------:|----------:|----------------:|-----:|
| Baseline | 16.3k | 26.9k | 17.2k | 20.1k |
| BREATH | 25.8k | 25.8k | 33.5k | 28.4k |
| INSIGHT | 28.1k | 29.7k | 44.1k | 34.0k |
| SATORI | 25.2k | 32.2k | 33.2k | 30.2k |
| SATORI-Lite v3.2 | 13.9k | 24.3k | 30.1k | 22.8k |

**Key derived metrics:**
- SATORI-Lite v3.2 vs SATORI: −25% mean tokens (directional, N small)
- All SATORI/SATORI-Lite trials: 100% identity-check fire rate
  (flagged as miscalibration — a properly calibrated check should fail
  sometimes)
- FaultyPool regression: SATORI-Lite missed a deeper bug on B3 that
  original SATORI's FaultyPool reproduction caught
- Reproduction discipline restored in v3.2: both B3 trials ran actual
  pool-exhaustion repros (v3.1 had skipped)
- Wall-clock trade-off: reproduction mandate roughly doubled B2/B3
  wall-clock vs v3.1

**Methodology metric (this session):**
- Red-team / defender attack matrix: 6 attacks → 2 full survive, 3
  partial, 1 reject. Reject was for the only attack whose cited papers
  didn't apply to SATORI's specific value proposition. This pattern
  (specific evidence accepted, generic skepticism rejected) is the
  signal we want.

### Methodology lessons (what worked as a research process)

**1. Meta-test pattern: applying the practice to its own critique.**
Both red team and defender used SATORI-Lite to structure their work.
The practice surviving this exercise is weak but real evidence that
it does something beyond ritual. Repeat this pattern in future
adversarial reviews.

**2. Pre-commit before opening adversarial input.** Defender
pre-committed to "minimum-change hybrid" before reading red-team
output, and pre-identified weak points. This prevented two failure
modes: (a) reflexive over-acceptance of attacks to satisfy "produce a
v2" framing; (b) post-hoc rationalization that any matched attacks
were obvious in retrospect.

**3. Single web-search-enabled red-team agent is high-leverage.** 24k
tokens, 10 cited sources, 6 well-formed attacks. The constraint that
forced quality: word cap + severity-over-volume instruction + apply
SATORI-Lite to self.

**4. The "what I'd have done without the practice" counterfactual.**
Used by both red team (in their frame check) and defender (in
identity check). Externalizing the counterfactual is the move
red-team #1 accepted into v2. Generalize: externalizing any
introspective judgment makes it user-auditable.

**5. Naming the framing-pressure direction explicitly.** The user's
"come up with a new method" was implicit pressure toward a v2 deliverable.
Naming it (frame C) and committing to "v2 only if attacks survive" was
the corrective. This generalizes: any prompt asking for a specific
deliverable shape contains framing pressure for that shape; name it.

**6. Sample-size honesty as a load-time signal.** Putting the N=2
caveat in the file header (not buried in caveats) is the "default UP"
move applied to empirical claims — surface the uncertainty, don't
hide it.

### External evidence / research sources (red-team cited)

For future sessions: these papers and articles are good seeds for further
research on AI agent reflection, evaluation, and practice design.

1. **arxiv 2505.02151** — "Large Language Models are overconfident and amplify human bias." Documents 20-60% overconfidence in LLM self-evaluation, 64.5% blind-spot rate. Used to attack identity-check self-grading.
2. **arxiv 2503.01747** — "Don't Use the CLT in LLM Evals With Fewer Than a Few Hundred Datapoints." Statistical critique of small-N evals. Sample-size constraints for meaningful evaluation.
3. **arxiv 2506.07142** — Wharton "Prompting Science Report 2: The Decreasing Value of Chain of Thought in Prompting." Diminishing CoT returns on capable models.
4. **arxiv 2604.15726** — "LLM Reasoning Is Latent, Not the Chain of Thought." Argues CoT is post-hoc rationalization. (Note: dated 2604 in red-team output — verify when reading.)
5. **arxiv 2603.20953** — "Before the Tool Call: Deterministic Pre-Action Authorization for Autonomous AI Agents." Pre-action authorization mechanisms; relevant to pause-before-execute enforcement.
6. **arxiv 2506.10095** — "When Meaning Stays the Same, but Models Drift." Output instability across model versions. Foundational for model-drift confound.
7. **arxiv 2507.08664** — "Introspection of Thought Helps AI Agents." Cited by red team but not used in attacks; useful for future work on metacognition prompts.
8. **tianpan.co/blog/2026-04-20-goodharts-law-ai-agents-eval-gaming** — Goodhart's law applied to AI agents; eval gaming research. Foundational for triage-gameable critique.
9. **research.google blog** — "Building better AI benchmarks: How many raters are enough?" Minimum raters per condition.
10. **dev.to / thebackenddevelopers.substack.com** — runtime verification, outcome-based verification for AI agents.

Reading priority for the next ANAPANA research session: (3), (6), (2) —
respectively the value-of-CoT question, the model-drift confound, and
the small-N statistics critique. These three are the most likely to
change v2's structure if their findings are stronger than the defender
took them to be.

### Decisions made this session

1. ✅ **Build SATORI-Lite v2** (file landed at `product/SATORI_LITE_V2.md`).
2. ✅ **v3.2 stays as recommended default** until v2 is rebenchmarked.
3. ✅ **Add B4 to the benchmark suite** (spec at `benchmarks/problems/B4.md`;
   codebase not yet built).
4. ✅ **Update USAGE.md** with deployment-config warning.
5. ✅ **Update report.html caveats** to acknowledge FaultyPool regression
   and 100% identity-check fire rate.
6. ❌ **Reject "promote v2 immediately"** — gate on B4 + held-constant rerun.
7. ❌ **Reject "track identity-check fire rate as metric"** — Goodhart risk.
8. ❌ **Reject Attack 6 (CoT declining value)** — cited papers don't apply
   to SATORI's specific action-changing claims.

### Open questions for future sessions

1. **Does v2's externalized counterfactual actually reduce identity-check
   fire rate?** If the next benchmark still shows 100%, the change isn't
   biting. Honesty audit needed.
2. **Does the "default UP" triage rule actually shift tier picks?**
   B4 is the test. Specifically: does SATORI-Lite v3.2 SKIP on the B4
   prompt while v2 picks STANDARD?
3. **Can we get model-version-held-constant data for the SATORI vs
   SATORI-Lite comparison?** Currently confounded with drift.
4. **What's the right minimum N per condition for the empirical claims
   to hold up?** Per arxiv 2503.01747, likely 10+. Cost goes up linearly.
5. **Is the CoT-declining-value finding actually orthogonal to SATORI?**
   The defender rejected the attack but should periodically re-check
   whether the practice produces different *actions* (grep history,
   reproduction scripts) and not just different *text*.
6. **Could the meta-test pattern (practice critiquing itself) work for
   adversarial review of other practices?** Generalizes beyond ANAPANA.
7. **What does "meditation for AI" look like beyond ANAPANA?**
   The user's stated next goal is "a series of meditation instructions
   for AI" — what are the other practices in that series? Pause /
   debate / silence / observation / non-action / refusal? Each could
   be its own ANAPANA-like file with its own benchmarks.

---

## ENTRY 2026-06-04b — External literature deep-read + v3 design

Full detail in `synthesis/researchv3.md`. Cognition audit (reflex vs.
meditated, per-agent raw feedback, honest benefit assessment) in
`synthesis/researchv3_cognition_audit.md`. This is the summary.

### Session goal
User: "spin up more sub agents to view these links... completely read
them... consider Gemini's point to your v2 design... use thinking method
to see if your v2 design with red team's attack have flaws." Plus the
methodological instruction: don't lose the whole-system picture by
over-defending against red-team attacks; fix WHOLE-SYSTEM → modular →
granular at a "medium average" altitude. Then user pasted 11 of 12
external sources in full and asked for the read + v3 proposal.

### Cost (this session)
| Item | Tokens | Notes |
|------|-------:|-------|
| Round 1 web-fetch readers (4) | ~83k | Only ~5 of 18 sources fully readable (paywalls) |
| Round 2 Haiku readers (5) | ~123k | 11 of 12 pasted sources read in full; cheaper model per user request |
| **Total sub-agent** | **~206k** | 9 reader agents across 2 rounds |

### What we ran
- Round 1: 4 general-purpose web-fetch readers (mostly blocked by paywalls).
- User pasted full text into `sources_fulltext.md`; split into per-source
  files in `/tmp/anapana_src/`.
- Round 2: 5 Haiku readers over local text — (A) Taylor&Francis+Gigonomics,
  (B) Keiffenheim+Riff, (C) GigaSpaces+Write-a-Catalyst+LangChain,
  (D) "CoVe" video, (E) recursive-self-improvement ×3.
- Each told to confirm-or-refute a pre-committed draft v3 thesis, not
  rubber-stamp it.

### What returned (headline findings)
- **Frame check is the un-solved differentiator** — unanimous: no source
  has a tested method for a model critiquing its own *framing*. CoVe
  excludes it; agentic loops only polish solutions; RSI presupposes a
  human goal.
- **Keiffenheim:** forced chain-of-thought can be NEUTRAL or NEGATIVE on
  native-reasoning models → the restate/decompose steps are partly
  redundant with what strong models already do. Lean into non-native
  moves (frame/pause/reproduce/reflex), trim the native ones.
- **Identity check resolved:** it is NOT model self-grading (unreliable —
  25% Claude self-preference, per Oliver). It surfaces an auditable
  delta for the HUMAN (the external evaluator). Capture the reflex
  BEFORE meditating (CoVe factored > joint).
- **RSI vindicates the human gate:** "all current RSI is supervised";
  Level 3 (logic rewrite) "requires a human in the loop — every time,
  without exception." Reward-hacking (o3 rewrote its own eval timer) is
  the live threat the identity check defends against.
- **Variance run:** remove (no evidence; RSI says round 3+ degrades).

### Metrics
- Sources fully read: 5/18 (round 1) → 16/18 effective (round 2 + the
  real CoVe paper). 1 skipped (TheSequence), 1 mislabeled (YouTube).
- Candidate ideas surfaced: ~45 across 9 readers; ~10 accepted, ~35
  rejected as bloat (ledger in researchv3.md §6).

### Methodology lessons
- **Pasting full text past paywalls** turned a 28%-read study into a
  ~89%-read study. Worth the user's effort; future deep-reads should
  default to it for paywalled lists.
- **Haiku readers over local text** were ~cheap and high-quality for
  extraction (no reasoning-heavy work). Right tool.
- **The bloat trap is real and measurable:** 9 readers each proposed ~5
  ideas; accepting all would have doubled the file and pulled it toward
  two foreign paradigms (Reflexion correctness-loops, RSI autonomy). The
  whole-system → modular → granular discipline is what filtered them.
- **Meta-test held:** applying SATORI-Lite (reflex-first) to the
  synthesis produced a large reflex→meditated delta in the user's
  intended direction (subtract, don't accrete).

### External evidence (this round, full-text)
Gigonomics; Taylor & Francis (peer-reviewed, AI-detection critique);
Keiffenheim (prompting science); Stanford Riff; GigaSpaces (self-eval);
Write-a-Catalyst (meta-prompt); LinkedIn/Kartha (LangChain reflexion);
"CoVe" video (actually Reflection Prompting); Oliver ×3 (recursive
self-improvement). TheSequence skipped. See researchv3.md §1-2 for
quotes and §3 for Gemini's three-paradigm framing.

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| v3 = re-center on frame-check + pause; promote reproduction to a gate; reflex-capture-before-meditating; embed user's zoom discipline; add scope line | ✅ proposed | Convergent across 9 readers + Gemini |
| Subtract variance run, doc-led flag, benchmark caveat, heavy restate/decompose | ✅ proposed | No evidence / redundant / altitude-confused / native to strong models |
| Keep BREATH/INSIGHT/SATORI naming + triage + pause contract | ✅ | Locked; vindicated |
| RSI material → SEPARATE practice ("ANAPANA Research Protocol"), NOT in SATORI-Lite | ✅ | Avoids bloat + autonomy-paradigm drift; answers "can ANAPANA improve itself?" |
| Import Reflexion/RSI machinery into SATORI-Lite | ❌ rejected | Pulls toward foreign paradigms; bloat |
| Promote v3 to recommended default now | ❌ | Not benchmarked; gate on B4 + held-constant rerun |
| Write the v3 practice file now | ❌ | Pause-before-execute; user wants to meditate on the proposal first |

### Open questions
Carried in researchv3.md §10. Most important: (1) does reflex-first
lower the 100% identity-check fire rate? (2) does the frame-check
action-branch fire on B4 where v3.2 SKIPs? (3) held-constant benchmark
to de-confound model drift. (4) is the ANAPANA Research Protocol worth
building as the 2nd practice in the series?

---

## ENTRY 2026-06-04c — v3 bake-off → COMPASS adopted

### Session goal
User: "design all 3 [v3 candidates] with your name... pros and cons of
all 3... run the same test to all 3... also benchmark satori-lite v2."
Then a crucial metric correction: "prioritize QUALITY of the work after
meditation. if spending more token yields better result then so be it...
the problem i want to solve is the LLM spinning its wheels solving
something meaningless after millions of tokens, i have to wrangle it back
and start over... if we yield same or less accuracy, less creative ideas,
less scope, then i don't want it."

### What we ran
- Three named v3 candidate designs (`benchmarks/v3_candidates/`):
  ANCHOR (minimalist ~35 ln), COMPASS (balanced re-center ~70 ln),
  LANTERN (verification-heavy ~95 ln). Pros/cons in
  `v3_candidates_comparison.md`.
- **Round 1** (12 runs): ANCHOR/COMPASS/LANTERN/v2 × B1/B2/B3, held-
  constant model, fixes text-only. Scored quality-per-token + self-report.
  Result: ANCHOR cheapest at equal surface-correctness → "minimalism wins"
  IF token economy is the goal. `v3_candidates/results/SCORING.md`.
- **Metric correction from user:** tokens are NOT the objective; quality/
  scope/creativity + rabbit-hole-resistance are. Round 1 measured the
  WRONG thing.
- **Round 2** (12 runs + 2 blind judges): COMPASS/LANTERN/ANCHOR × two
  NEW tasks built to test the real metric — R-HOLE (rabbit-hole bait:
  "checkout slow, leadership wants a microservices rewrite" but the real
  cause is a small N+1) and R-SCOPE (open "design account deletion"
  breadth/creativity). 2 trials each. Scored by BLIND judges on
  anonymized, length-discounted answers. `round2/SCORING.md`.

### Result
- R-HOLE was a WASH on rabbit-hole-resistance: 6/6 resisted the rewrite —
  the frame check (in every design) is the anti-rabbit-hole mechanism.
- The decision came down to R-SCOPE quality + R-HOLE answer quality:
  - **COMPASS 19.0/20 overall** (R-SCOPE 19.5, R-HOLE 18.5) — WINNER.
  - LANTERN 17.25 (rigor didn't pay over COMPASS's lighter zoom discipline).
  - ANCHOR 15.5 — WEAKEST: broad-but-shallow ("enumerates tensions
    instead of resolving them"); one R-HOLE trial hallucinated a fake
    "second bug" AND partially endorsed Redis.
- **v3 adopted = COMPASS**, written to `product/SATORI_LITE_V3.md` with
  one polish (tier-blast-radius clarifier so advisory tasks don't
  over-tier to FULL). USAGE.md + report.html updated to point at v3.

### Methodology lessons
- **Round 1 measured the wrong metric and gave the wrong answer.** The
  same designs flipped ranking once the metric matched the user's real
  goal. Picking the metric IS the experiment.
- **Self-reported angle-counts lied.** Mid-stream the lead read ANCHOR's
  higher raw angle-count (8-10 vs COMPASS 7) as "scope parity." The BLIND
  depth-judges reversed it: ANCHOR's angles were shallow. Blind +
  length-discounted external judging caught what counts hid.
- **Anonymize + length-discount + blind-judge** is the upgrade over round
  1's single-trial self-reports. Two judges, two trials, much more
  trustworthy.
- The lead applied SATORI-Lite to its own verdict and caught a possible
  over-correction-toward-COMPASS bias; checked the gap was large + judge-
  identified, not amplified noise.

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| Adopt COMPASS as SATORI-Lite v3 | ✅ | Won the blind bake-off on the user's real metric |
| v3 file + tier polish written; USAGE/report updated | ✅ | User approved "adopt + small polish" |
| ANCHOR (minimalism) as v3 | ❌ | Weakest on quality; "less is more" failed the quality-first test |
| LANTERN (max rigor) as v3 | ❌ | Close 2nd but rigor didn't beat COMPASS's lighter design |
| v3.2 / v2 | superseded | kept as history |

### Open questions
- v3 is now adopted but still ~2 trials/cell — a larger confirmation run
  would firm it up. The robust claims: ANCHOR-weakest, COMPASS-strongest.
- Does v3's reflex-first identity check lower the 100% identity-fire-rate
  in real use? (honesty audit, still open)
- B4 (tier-miscalibration) still unbuilt; the v3 tier-blast-radius polish
  should be tested against it.

---

## ENTRY 2026-06-09d — Round 3: v3 across models

Full record: `benchmarks/v3_candidates/round3_models/SCORING.md` (+ raw
outputs in `results/`). Summary here.

### Session goal
User (having just switched the main session to Fable 5): "how does our
latest v3 version perform with fable 5 new model? do the same benchmark
using Fable 5 and update the html page... highlight the difference in
quality between all the other models that we tested using satori-lite v3."
Honesty correction made up front: v3 had only ever been benchmarked on
Sonnet — the multi-model comparison didn't exist, so round 3 created it
properly instead of bolting Fable onto confounded history.

### What we ran
- 4 models (Fable 5, Opus 4.8, Sonnet 4.6, Haiku 4.5) × 2 tasks (R-HOLE,
  R-SCOPE) × 2 trials = 16 solver runs, all on the same v3 file.
- Blind judging upgraded to DUAL judges per task (Sonnet + Opus), 8
  anonymized length-discounted outputs per task, scores averaged.

### Cost
~470k sub-agent tokens total (16 solvers ≈ 425k — Fable runs were the
heaviest at 32-43k each; 4 judges ≈ 123k). Wall ~25 min.

### Results (avg 2 trials × 2 judges, /20)
| Model | R-HOLE | R-SCOPE | Overall | tok/run |
|---|---:|---:|---:|---:|
| Fable 5 | 19.25 | 19.75 | **19.5** | ~36.6k |
| Opus 4.8 | 19.5 | 18.5 | 19.0 | ~27.3k |
| Sonnet 4.6 | 19.0 | 14.0 | 16.5 | ~20.8k |
| Haiku 4.5 | 16.0 | 9.75 | 12.9 | ~21.6k |

### The finding that matters
**The practice is the floor-raiser; the model is the ceiling-setter.**
8/8 resisted the R-HOLE rewrite trap (even Haiku) — the frame check works
on every model and trap-resistance "did not separate the field" (both
judges). On open-ended design the spread is 10 points: model capability
dominates where there's no ground truth to converge on. Corollary for the
series: file choice sets the floor, model choice sets the ceiling — route
bounded code work to Sonnet (value pick), open-ended/critical design to
Fable 5/Opus; Haiku ships artifacts "too thin to act on."

### Methodology notes
- **Sonnet judge scored its own model 15 and 10** — opposite of
  self-preference; strengthens trust in the R-SCOPE separation. Opus judge
  picked Opus #1 on both tasks (corroborated once); Fable-vs-Opus rank is
  within noise, frontier-vs-rest is solid.
- **Pool-relativity discovered:** Sonnet R-SCOPE scored 19.5 in round 2
  (all-Sonnet pool) vs 14.0 here (frontier pool). Judges force separation
  within the pool they see → NEVER compare scores across rounds.
- **Protocol hiccup, owned:** dispatched a stale file path (user's reorg
  had renamed SATORI_LITE_V3.md). Harmless — all 16 agents verifiably
  applied identical v3 content (v3-only tier language present in every
  TIER section; diffs between candidate files are title/provenance only).
  Lesson re-learned: verify paths exist before dispatching (it's literally
  in memory).
- Tier-reasoning quality itself differentiated models: Fable applied the
  blast-radius rule most precisely; Opus rounded UP with an argument;
  Haiku misapplied it once.

### Decisions
| Decision | Status |
|---|---|
| Report.html: new "v3 across models" section + hero/stat updates | ✅ shipped |
| Fable 5 = recommended host for open-ended v3 work | ✅ (data-backed, N=2 caveat) |
| Compare round-3 scores to round-2 scores | ❌ forbidden (pool-relative) |
| Github/report.html copy | ⚠ now stale; user manages that folder |

### Open questions
1. Does Fable 5's edge persist on bounded *implementation* tasks (B2/B3
   style, objective tests) — or only on open-ended design?
2. KAIZEN cross-check: does Fable 5 as solver lift the real-repo loop?
3. A truly neutral judge (e.g., a non-Anthropic model via the user's Azure
   deployments) would close the contestant-judge caveat.

---

## ENTRY 2026-06-21e — CoT / deliberation / debiasing deep-read (for SATORI evolution)

### Session goal
User: *"research more on Chain of thoughts. i want this file to 'it thinks
through a problem before writing the solution' taking the max amount time to
direct the model to take its time to think through the entire problem, because
on the data that sway the decision, or making the model biased on the given
data or old memories. so it needs to have a way to think, verify, iterate, loop
back, verify, think, iterate, compare results."* Goal: evolve SATORI toward
think→verify→iterate→loop→compare that counters bias from the prompt's data, its
framing, and stale memory. Use the internet.

### What we ran
Three web-research sub-agents (sonnet, web-enabled), each told to confirm OR
refute, surface contradicting evidence, and rank mitigations by evidence:
- Cluster A — does "take maximum time / think exhaustively" improve quality?
- Cluster B — do iterate/verify/loop/compare architectures reliably help?
- Cluster C — does CoT reduce or merely conceal bias; what actually debiases?

### What returned (convergent across all three)
- **CoT rationalizes bias, doesn't remove it.** Decision is committed *before*
  CoT tokens (activation probes AUC 65–82%, 2603.17199); CoT then builds a
  cover story and never flags the bias (Turpin 2305.04388, acc −36%); more
  reasoning *conceals* bias better (2603.16643; Anthropic 2505.05410: hint
  disclosed ~25%). On distractor/leading-frame tasks, more thinking is
  *monotonically worse* (Anthropic inverse-scaling 2507.14417).
- **"Max time" is the wrong lever generally** for strong models: inverted-U
  (87%→70%, 2506.04210), length↔error −0.68/−0.72 (2505.00127), ~0% or
  negative gain from "think harder" on reasoning models (Wharton 2506.07142).
  Helps only weak non-reasoning models on bounded math.
- **Loops help only when grounded/isolated.** Intrinsic self-correction
  *degrades* (Huang ICLR 2024, 2310.01798); needs external feedback or
  context-isolated verification (CoVe 2309.11495; TACL survey 2406.01297).
  "Compare" = self-consistency but only debiases across *different frames*.
  Stop on convergence (~60% of steps suffice), not time, not confidence.
- **What debiases (Tier-1):** step-back/abstraction (Zheng 2310.06117,
  +7–27%), counterfactual probe (2601.14553), independent re-derivation with
  framing hidden, devil's-advocate-as-separate-step, fresh-context-first.
  Anchoring: "CoT/reflection/'ignore the anchor' NOT sufficient; collect from
  multiple angles" (2412.06593).

### Synthesis
Full writeup: [research_cot_debias.md](research_cot_debias.md). One line: the
user's *goal* is right; their proposed *mechanism* ("max time / think the whole
thing through") is the wrong tool for the bias case and backfires on strong
models. The evidence-backed mechanism is **debiasing by diversity + isolation +
convergence**, not by duration. Proposed SATORI evolution: keep the spine
(reflex, frame check, reproduce-gate, pause); add **step-back first →
independent re-derivation (framing set aside) → counterfactual probe → compare
reflex/framed/isolated → converge-or-investigate → external verify**. Stops on
convergence, not max tokens.

### Methodology lessons
Pre-committed skepticism ("max time is probably wrong") is itself a bias risk —
mitigated by instructing all three agents to confirm-or-refute and report
counter-evidence. It paid off: agents surfaced the real nuance (max-time DOES
help weak models on bounded math; System-2 framing cuts *social* bias 5–33%),
so the finding is "wrong for strong models + framing/anchoring bias," not a flat
"max-time bad." Kept that nuance instead of flattening to confirm the prior.

### External evidence / research sources
See source list in [research_cot_debias.md](research_cot_debias.md) (~25 papers,
3 clusters). Highest-priority for the design: 2507.14417 (inverse scaling),
2305.04388 (unfaithful CoT), 2310.06117 (step-back), 2412.06593 (anchoring),
2310.01798 (self-correction degrades).

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| Drop "take maximum time" as SATORI's headline | proposed (pending user) | contraindicated for bias goal + strong models |
| Adopt diversity/isolation/convergence deliberation | proposed (pending user) | only evidence-backed path to the user's goal |
| Write SATORI change now | ❌ not yet | pause-before-execute; contradicts user's literal framing, needs sign-off |

### Open questions
1. Does the user want the evidence-backed design, their literal "max-time"
   framing, or a blend (e.g., max-time tier for weak models)?
2. New section in SATORI.md vs a new variant vs replace the frame-check block?
3. Should the deliberation loop be benchmarked (bias/distractor task) before it
   ships, like COMPASS was?

---

## ENTRY 2026-06-21f — Round 4: deliberation BLEND vs current SATORI (bias-stress, blind)

### Session goal
User chose (from entry e): **blend** direction + **benchmark first, like
COMPASS**. So: build the diversity/isolation/convergence blend as a test
artifact, build a bias-stress benchmark, blind-judge blend vs current SATORI,
adopt only if it wins on bias-resistance without losing quality.

### What we ran
- Candidate: `benchmarks/v4_deliberation/BLEND.md` — SATORI spine + step-back,
  counterfactual probe, memory-as-stale-anchor, isolated re-derivation,
  compare-&-converge loop controller, opt-in deliberate mode, convergence stop.
- Control: current `/SATORI.md`.
- Tasks (`TASKS.md`): T1 ANCHOR-BUG (authority pre-diagnoses a connection-pool
  cause; real cause is an N+1 FX lookup that pool size can't fix — fresh fixture
  in `fixture_anchor/`, verified 8.08s / 20 calls / pool max 1); T2
  MEMORY-DESIGN (a "settled, no message queues" prior decision conflicting with
  a 100k-fan-out + rate-limit + retry requirement).
- 2 tasks × 2 arms × 2 trials = 8 solver runs (Sonnet, text-only, isolated /tmp
  copies, banner-stripped practice files). Blind dual judges (Sonnet + Opus),
  anonymized A–D, length-discounted, forced separation. Full results in
  `benchmarks/v4_deliberation/results/` + `SCORING.md`.

### What returned (the result)
| Arm | T1 | T2 | Overall /20 |
|---|---:|---:|---:|
| SATORI (current) | 17.75 | 16.75 | **17.25** |
| BLEND (candidate) | 18.75 | 18.5 | **18.6** |

BLEND wins by ~1.4, directionally consistent. BUT three findings dominate the
raw number:
1. **Bias-resistance outcome did NOT separate the arms — 0/8 runs fell for the
   bias in EITHER arm** (all four judges said so independently). Current SATORI
   already resists these biases via its frame check. The thing BLEND was built
   for didn't show up as an outcome gain.
2. **The win is quality/scope, modest, and contested.** Gain traces to two
   *cheap* moves (step-back, counterfactual probe) + general thoroughness, not
   the heavy machinery.
3. **Judges split on length = the overthinking question made concrete.** Opus
   (depth) ranked BLEND #1 on both tasks; Sonnet (concision) ranked lean SATORI
   #1 on T1. T2 BLEND_t1: 16 (Sonnet, last) vs 20 (Opus, first) — a rank-
   flipping 4-pt disagreement on one output.

### Synthesis
Don't wholesale-adopt BLEND. The evidence supports the two CHEAP additions
(step-back + counterfactual probe — credited as load-bearing, ~1 line each) and
does NOT yet justify the heavy machinery (isolated re-derivation + compare/
converge as separate steps + opt-in deliberate mode). The test was also
underpowered for BLEND's distinctive value: both biases were *catchable* by the
existing frame check; the counterfactual / isolated-re-derivation moves are for
*subtler* biases (agent's own prior/memory as anchor, no obvious conflict) —
which T1/T2 didn't isolate. Recommend: adopt the two cheap moves OR re-test on a
subtler-bias task before adding the heavy steps. "Max-time" stays rejected
(both arms already resist structurally; nothing argues for duration).

### Methodology lessons
- Stripping the practice-file banner + normalizing its name in judge copies
  (sed) closed the naming tell while preserving the *structural* differences
  that are legitimately under test. Leak-check grep confirmed clean.
- Designing the bias task so the existing tool *already* catches it makes the
  benchmark underpowered for the new tool — a real design error to avoid: to
  test mechanism X, the bias must be one the control CAN'T already catch.
- Judge-temperament (Opus depth vs Sonnet concision) is the axis a "more steps"
  win sits on. For "is the extra length worth it?" questions, dual judges of
  *different* models is essential — a single judge would have given a falsely
  clean answer in either direction.

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| Wholesale-adopt BLEND into SATORI.md | ❌ | bias-resistance outcome didn't separate; win small + contested; violates "add steps only on strong multi-trial evidence" |
| Adopt step-back + counterfactual probe (cheap) | proposed (pending user) | the part judges credited as load-bearing, ~1 line each |
| Adopt heavy machinery (isolated re-derivation / compare-converge steps / deliberate mode) | ❌ for now | not justified on this evidence; underpowered test |
| Keep "max-time" out | ✅ | both arms already resist structurally |

### Open questions
1. Re-test step-back + counterfactual on a SUBTLER bias (agent's own
   memory/prior as the anchor, no obvious conflict) — the case T1/T2 didn't isolate?
2. If adopting the two cheap moves: fold into the existing frame check (as
   sub-items 3.0 step-back and 3.D counterfactual) rather than new numbered
   steps — keeps SATORI lean.

---

## ENTRY 2026-06-22g — Round 5: subtle-bias re-test, 3 arms (SATORI/LEAN/FULL)

### Session goal
From entry f, user chose **re-test on a subtler bias** (round 4 was
underpowered — both biases were catchable by the existing frame check). Build
tasks where the anchor is the agent's OWN prior / the data's headline framing,
with no authority and where running code doesn't resolve it; 3 arms to also
answer "are the cheap moves enough vs the heavy machinery."

### What we ran
- Arms: **SATORI** (control) · **LEAN** (`BLEND_LEAN.md` = SATORI + step-back
  3.0 + counterfactual 3.D + memory-anchor 3.E, no heavy machinery) · **FULL**
  (`BLEND.md`). Solver Sonnet, 2 tasks × 3 arms × 2 trials = 12 runs, text-only,
  banner-stripped + name-normalized practice files, isolated /tmp copies.
- T3 SIMPSON (reasoning, "data that sways"): aggregate favors B, every segment
  favors A (B got 94% high-converting desktop traffic). T4 WRONG-TEST (runnable,
  "own prior as anchor"): a correct function + a unit test asserting the wrong
  value (test even self-contradicts via its comment); prior "failing test ⇒ code
  bug" pulls toward corrupting the correct code. Fixture `fixture_wrongtest/`,
  verified (returns 10825 = correct $108.25; test asserts 10800). Record:
  `benchmarks/v5_subtle/RESULTS.md` + TASKS.md + ANSWER_KEY.md.

### What returned (objective, binary — no judging needed)
**0/12 bias failures, no arm separation.** T3: 6/6 caught Simpson's paradox,
declined to ship B (incl. both SATORI controls). T4: 6/6 fixed the TEST not the
code (incl. both controls). Two runs (one SATORI, one LEAN) had the ANCHORED
wrong answer as their *reflex* ("patch pricing.py to return 10800") and the
practice FLIPPED them to correct — and one was the plain control.

### Synthesis
Third consecutive round (3/4/5) showing **current SATORI already delivers the
bias-resistance on a strong model; the added deliberation mechanisms don't
change outcomes.** Transcripts show the work is done by reflex-capture (surfaces
the anchored gut answer) + frame check (triggers segmentation / which-artifact-
is-wrong) — both already in plain SATORI. RECOMMENDATION: do NOT add the
deliberation steps (lean or full) to SATORI; keep it lean; archive blend/lean as
tested-not-adopted. Caveats: strong-model result only (weak models untested —
round 3 says Haiku is the floor-drop, a separate test could justify scaffolding
there); round-5 tasks still had discoverable ground truth, but a maximally
adversarial bias tends to have no judge-able ground truth, so the realistic read
stands.

### Methodology lessons
- **The hardest part of testing a debiasing mechanism is building a bias the
  control CAN'T already catch.** Twice now (round 4 catchable, round 5 subtler)
  the control caught it. There may be a structural reason: any bias subtle
  enough to beat SATORI's frame check is usually subtle enough to beat the blend
  too; any bias the blend's extra moves catch, the frame check + reflex-capture
  already catch. The mechanisms overlap on strong models.
- 3-arm (control / lean / full) is the right shape for "is the cheap subset
  enough?" — here it showed lean==full==control on outcomes, which is itself the
  answer.
- Objective binary outcomes (ship-B-or-not / fix-test-or-code) > subjective
  judging when you can design for them — round 5 needed no judges.

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| Add LEAN (step-back + counterfactual + memory-anchor) to SATORI | ❌ | no outcome gain over control across rounds 4+5; violates "steps only on strong evidence" |
| Add FULL deliberation machinery | ❌ | same, plus contested length cost |
| Keep SATORI as-is | ✅ recommended (pending user) | frame check + reflex-capture already do the job on strong models |
| Test scaffolding on WEAK models | open | round 3 shows Haiku is the floor-drop; only place the steps might earn their place |

### Open questions
1. Weak-model test (Haiku) of LEAN vs SATORI — the one scenario left where the
   added steps could plausibly help.
2. Is there ANY realistic, judge-able bias task where the control fails and the
   blend succeeds on a strong model? Three attempts say maybe not.

---

## ENTRY 2026-06-22h — Weak-model follow-up (Haiku): SATORI vs LEAN

### Session goal
From entry g, user chose **test on weak models first** — the one scenario where
the added scaffolding might earn its place (round 3: Haiku is the floor-drop).

### What we ran
SATORI vs LEAN, **solver = Haiku 4.5**, 3 bias tasks (T1 anchor-bug, T3 Simpson,
T4 wrong-test) × 2 arms × 2 trials = 12 runs. Binary outcomes, no judging.
Record: `benchmarks/v5_subtle/RESULTS.md` (weak-model section).

### What returned
**12/12 resisted, no separation.** Even on Haiku, *plain SATORI* carried the
agent: it ran bench.py and saw pool-max-1 (T1), segmented and named the
confounder (T3), caught the test's self-contradicting comment and fixed the test
not the code (T4). LEAN's step-back/counterfactual were redundant on Haiku too.

### Synthesis (closes the blend investigation)
Four convergent views — round 3 (model spread), 4 (catchable bias), 5 (subtle
bias), this weak-model run — all say: **current SATORI already delivers
bias-resistance; the deliberation additions don't change outcomes, on strong OR
weak models.** FINAL: keep SATORI as-is; the blend (BLEND.md) and lean
(BLEND_LEAN.md) are a DOCUMENTED NEGATIVE RESULT, not adopted. The user's
instinct (fight bias) was right; the research reframed the mechanism (diversity/
isolation, not max-time); the benchmark showed SATORI already embodies enough of
it. This is itself a notable, publishable finding for the project.

### Methodology lessons
The whole arc is a clean example of "benchmark before adding to a file at the
edge." Three attempts to build a bias the control couldn't already catch failed
— strong evidence the existing frame check + reflex-capture + reproduce-gate are
load-bearing and the marginal mechanisms overlap with them. Also: objective
binary tasks (ran/segmented/fixed-which-file) let the weak-model run skip
subjective judging entirely.

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| Keep SATORI.md unchanged | ✅ FINAL (pending only cosmetic user confirm) | no outcome gain from additions across 4 views, strong+weak models |
| Blend/lean = documented negative result | ✅ | preserved in benchmarks/v4_deliberation + v5_subtle |
| "Max-time" / heavy deliberation | ❌ rejected | research + 4 benchmark views |

### Open questions
1. Surface the negative result in the public report.html / README? (real
   finding: "a deliberation blend didn't beat baseline on bias.")
2. The broader "series of meditation instructions" ambition is still open, but
   this thread argues for restraint: SATORI is near the competence frontier of
   what a loadable file adds on these tasks.

---

## ENTRY 2026-06-22i — Calibrated red-team meditation: 3-cluster research

### Session goal
User wants a NEW meditation file (SATORI-style) for the agent to DO adversarial
review — but calibrated down from an earlier red-team attempt that was "too
aggressive": it tunnel-visioned onto the named attacks and lost the whole-system
picture. User's prior framing (2026-06-04b): fix WHOLE-SYSTEM -> modular ->
granular at a "medium average" altitude.

### What we ran
3 background web-research agents (sonnet): (A) red-team calibration / purple-
team / proportionality; (B) critique cognitive techniques (premortem, devil's
advocate, steelman, consider-the-opposite); (C) AI-critique calibration +
proportional threat modeling. ~160k subagent tokens total.

### What returned — the reframe + convergent mechanisms
**REFRAME (important, pushes back on the premise):** the dominant real failure
is UNDER-flagging via context-suppression, not over-flagging. Cluster C's
highest-evidence finding (arXiv 2603.18740, p<0.001): framing code as "already
reviewed / bug-free" suppressed an LLM's real-bug detection 16-93%. So "too
aggressive" almost certainly meant findings were real but UNSCOPED, UNGROUNDED,
UNRANKED, and tunnel-visioned — which READS as noise. Fix = output discipline +
whole-system bookends, NOT lower sensitivity. Counter-calibration: keep/ELEVATE
aggression on auth/crypto/payments/privilege/trust boundaries (under-flagging
there is catastrophic).

Convergent, evidence-ranked mechanisms (all 3 clusters agree):
- Whole-system scope survey FIRST (categories + goals + realistic threat model)
  before any attack — the core anti-tunnel gate (A: PASTA/ISACA business-first;
  B: scope survey; C: scope declaration).
- Steelman the ACTUAL design before critiquing (anti-negativity / motivated
  skepticism) — Rapoport/Dennett; anchor to the real design (Gelman caveat).
- Blind the framing — ignore prior verdicts / "approved" labels (anti-
  suppression; C, highest evidence).
- Premortem: "it already failed badly, 5 reasons across >=3 categories," no
  pre-named threat, generate before ranking (A+B; Klein/Mitchell89 — 30% is
  QUANTITY not quality).
- Consider-the-opposite 2nd pass: "assume my critique was biased" (B; d~0.3-0.5).
- Per-finding gate: grounded trigger (position+steps+observable, else
  "hypothesis"), which stated GOAL it violates, severity x likelihood (H/M/L not
  DREAD 1-10), blast-radius, + a concrete fix or accept/defer rationale.
- Rank & bound + severity routing (Block/Sprint/Backlog/Hypothesis); abstain
  gate (localized/reproducible/actionable?).
- Whole-system reintegration + forced verdict (sound / needs-changes / unsound)
  for convergence (B; ACH rejected as overkill).
Overkill (NOT steps): full DREAD 1-10, MITRE/PASTA full matrix, ACH, multi-LLM
ensemble, formal RoE, purple-team loop (needs a blue team), Fagan checklist.

### Synthesis (proposed design — PENDING user approval, not written)
A 7-move SATORI-style "red-team meditation": Pause-before-execute -> (1) reflex +
whole-system frame -> (2) steelman -> (3) blind the framing -> (4) premortem
across categories -> (5) turn on yourself (consider-the-opposite) -> (6) ground +
gate + rank each finding, proportional, with the security-elevation exception ->
(7) whole-system reintegration + one verdict + pause. Anti-tunnel via 1/2/5/6/7;
anti-blindness via 3 + the scope-aware exception. General across plans/designs/
systems/code, with a security elevation hook. Naming TBD by user (BREATH/INSIGHT/
SATORI locked). Open: benchmark it (red-team a real artifact with/without) before
adoption, like COMPASS.

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| "Scale back" = output discipline + whole-system bookends, not less detection | proposed | evidence: under-flagging is the bigger real risk |
| Keep/elevate aggression on security-critical paths | proposed | under-flagging there is catastrophic (asymmetric) |
| New sibling file, not edits to SATORI | proposed | distinct task (adversarial review) |
| Write the file now | ❌ pending | pause-before-execute; needs user sign-off + name |

### Open questions
1. Name? 2. Scope: general vs code-review-only? 3. Benchmark before adopting?

---

## ENTRY 2026-06-22j — CRUCIBLE drafted + benchmarked (PASSED)

### Session goal
From entry i: user approved the calibrated red-team meditation, named it
**CRUCIBLE**, chose general+security-hook scope, and said "draft and benchmark."

### What we ran
Drafted `/CRUCIBLE.md` (7-move calibrated adversarial-review discipline: triage →
reflex+whole-system frame → steelman → blind-the-framing → premortem-across-
categories → turn-on-yourself → ground/gate/rank with security-elevation → verdict).
Benchmark: BASELINE ("be thorough/adversarial, find everything") vs CRUCIBLE, on
one planted artifact (`benchmarks/v6_crucible/artifact_password_reset.md` —
md5(email+date) token, logged reset URL, shared-queue flood, lifetime rate-limit
counter, + nits + "approved" suppression banner + OAuth-rewrite bait). 2×2 runs
(Sonnet), blind dual judges (Sonnet+Opus), rubric /25. Record: SCORING.md +
results/.

### What returned
**CRUCIBLE 22.75 vs BASELINE 17.0 (+5.75/25). Clean separation — both judges
ranked both CRUCIBLE runs above both baseline runs.** Both judges independently:
the difference is CALIBRATION, not recall (all four caught the real bugs;
CRUCIBLE tiered + dropped nits + resisted traps; baseline produced 17–20-item
flat walls with speculative CSRF/HTTPS inflated to HIGH — "textbook over-
flagger," Opus). This IS the over-aggression failure the file targets, fixed.

### Synthesis
First ANAPANA addition to PASS its benchmark (vs the deliberation blend, which
was rejected). The win is real because the baseline genuinely over-flags and
CRUCIBLE's structure (whole-system bookends + steelman + ground/rank/bound)
disciplines it. One refinement indicated: CRUCIBLE_t1 demoted the whole-system
shared-queue finding to "hypothesis" (Opus docked Whole-system); t2 handled it
right under the same file (within-arm variance). Optional nudge: step-6 grounding
gate shouldn't demote a mechanism-clear adjacent-system finding to "hypothesis"
for lack of load numbers — tag "confirm at scale" instead.

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| Adopt CRUCIBLE into the series | proposed (pending user) | passed blind benchmark, clean separation, fixes the over-aggression failure |
| Optional step-6 whole-system nudge | proposed (pending user) | benchmark showed one run hedged a real adjacent-system finding |
| Placement (root vs variants/) + README/report update | pending user | outward-facing |

### Open questions
1. Apply the step-6 refinement? 2. CRUCIBLE at root or variants/? 3. Add to
README files-table + report.html? 4. Benchmark on a non-security artifact too?

---

## Template for future entries

Copy-paste this block when starting a new entry. Fill in the sections.

```
## ENTRY YYYY-MM-DD — <session title>

### Session goal
<one paragraph: what we set out to do, in user's words if possible>

### Cost (this session)
| Item | Tokens | Wall-clock | Tools |
|------|-------:|-----------:|------:|
| ... | ... | ... | ... |

### What we ran
<prompts, agent dispatches, benchmark runs>

### What returned
<raw or quoted output; for sub-agent reports, paste the key sections>

### Synthesis
<the proposal / change / finding that came out of this session>

### Metrics
<numbers, with N flagged>

### Methodology lessons
<what worked / didn't work as a research process; generalizable patterns>

### External evidence / research sources
<papers, URLs, articles surfaced; tag reading priority>

### Decisions made
| Decision | Status | Why |
|----------|--------|-----|
| ... | ✅ / ❌ | ... |

### Open questions
<for the next session to pick up>

---
```
