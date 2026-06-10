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
