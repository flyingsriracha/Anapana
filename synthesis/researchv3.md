# SATORI-Lite v3 — research record

Date: 2026-06-04. This is the detailed evidence record behind the v3
proposal. The structured summary lives in `research_log.md`; this file
is the deep version. The v3 *practice file* is NOT yet written — per the
pause-before-execute contract, v3 is a proposal to be meditated on first.

Inputs to this synthesis:
1. Four web-fetch reader reports from an earlier round (Riff/pedagogical,
   Reflexion/agentic, CoVe/verification, reflection-critique) — but that
   round only got ~5 of 18 sources fully (the rest paywalled/blocked).
2. **Five Haiku reader reports from this round**, reading 11 of 12
   sources the user pasted in full into `sources_fulltext.md` (raw text,
   no fetch failures).
3. Gemini's "three-paradigm" comparative analysis (user-supplied).
4. The lead's system-level pass, applying the user's own methodology
   (whole-system → modular → granular; fix at "medium average" altitude).

---

## 1. Access reality (honesty first)

The user pasted full text, which fixed the earlier access problem. Of the
12 paste slots:

| Source | Status this round |
|--------|-------------------|
| Gigonomics — AI skills that matter | FULL (was paywalled before) |
| Taylor & Francis — HE research evaluation (peer-reviewed) | FULL (was 403 before) |
| Eva Keiffenheim — Four prompting techniques | FULL (was paywalled) |
| TheSequence — Edge 401 | SKIPPED (user couldn't get it) |
| David Oliver — The Prompt That Improves Itself | FULL (was paywalled) |
| GigaSpaces — AI self-evaluation | FULL (was JS-blocked) |
| Write a Catalyst — Meta-prompt | FULL (was paywalled) |
| Stanford d.school — Riff | FULL (was auto-summarized) |
| LinkedIn — Self-reflecting agents (LangChain) | FULL (was login-walled) |
| YouTube — "CoVe" video | FULL transcript — but it's actually about Reflection Prompting, not CoVe |
| EXTRA: Three Levels of Recursive Self-Improvement (Oliver) | FULL (user-added) |
| EXTRA: Building a Self-Improving Agent w/ Claude Code (Oliver) | FULL (user-added) |

Two integrity notes carried from the prior round: (a) Gemini's arXiv ID
for CoVe (2504.16485) was wrong — resolves to an unrelated paper; the real
CoVe paper is 2309.11495, read in full last round. (b) The "CoVe" YouTube
video is mislabeled — it demonstrates the weaker joint-context Reflection
Prompting, not Chain-of-Verification.

---

## 2. Findings by cluster (this round)

### Cluster A — Peer-reviewed + human-skills (Taylor & Francis, Gigonomics)

**Gigonomics** ("AI skills that matter"): prompt engineering is dying;
the skills that survive are decomposition, evaluation, and taste.
- "Spending your time memorizing rigid prompt syntax today is like
  memorizing how to manually choke a car engine in the age of fuel
  injection."
- The vibe-check is a liability: "If you are using AI to categorize
  customer support tickets or summarize legal contracts, 'it looks okay'
  gets you sued." Fix = build a 50-example test set, measure a percentage.
- Reproduction-as-proof: "If you can walk into a meeting and say, 'I
  improved our AI sales bot's accuracy from 72% to 94%,' you are
  bulletproof. Everyone else will just be guessing."

**Taylor & Francis** (peer-reviewed; AI-detection in higher ed is
methodologically unsound): a 44k-char sustained dissection of
**confirmation bias as the core error mode**. Every validation technique
it debunks (linguistic markers, multiple detectors, base-rate-blind
flagging, hidden adversarial prompts) collapses into "building a case
instead of testing a hypothesis." Base-rate fallacy worked example: a
detector with 1% FPR flagging a paper can be anywhere from 47.6% to
97.5% likely correct depending on the unknown base rate — so the score
is meaningless without it. Core reframe: the institutional problem was
*framed* as "detect and punish" when the actual problem is "clarify
boundaries for hybrid authorship." That is a frame-check failure at
policy scale.

**Contribution to v3:** confirmation bias is the named enemy → the frame
check is the anti-confirmation-bias instrument. And: SATORI-Lite's
principles are **scale-invariant** (decompose, frame-check, measure,
pause apply to code, system design, *and* policy) — so v3 should carry a
one-line scope statement.

### Cluster B — Prompting-science + Riff (Keiffenheim, Stanford)

**Keiffenheim** (prompting tested under 25-100 trials):
- Structural constraints: evidence-backed (narrow the search space).
- Decomposition / chain-of-thought: **QUALIFIED** — "for non-reasoning
  models step-by-step prompts often improve accuracy, while for models
  with native reasoning capabilities they can be neutral or even reduce
  performance."
- Few-shot (show) >> persona (tell): "assigning an expert persona does
  not improve factual accuracy... they do not improve its epistemic
  competence (truth)." Politeness: inconsistent.
- The thesis line: **"You can't engineer a good prompt for a thought you
  haven't clarified. The quality of the output is tethered to the clarity
  of the intent behind it."**

**Riff** (Stanford reflection tool): interrogates, never prescribes ("not
intended to provide factual information... advice"). Bounded container:
"8 turns is a good target," "5-10 min." User stays in charge ("decide
when... diminishing returns and stop"). Two-level audit (the tool
reflects; a human audits the reflection). Four moves: elaborate/specify,
contrast/counterfactual, go beyond first impulse, project forward.

**Contribution to v3 — the sharpest insight of the whole study:** the
differentiators are **the moves the model does NOT do natively.** Strong
reasoning models already restate/decompose/consider — and forced CoT can
*hurt* them (Keiffenheim). What they do *not* do by default: question the
frame, pause before acting, run a reproduction, expose the pre-meditation
reflex. → v3 leans into the non-native moves and trims the native ones.

### Cluster C — Self-eval + meta-prompt + LangChain (GigaSpaces, Write-a-Catalyst, Kartha)

**GigaSpaces**: reliable self-evaluation "often powered by a secondary
model" + external signal; pure self-reflection risks rubber-stamping;
reliability is task-dependent ("especially in structured or repetitive
tasks").

**Write a Catalyst** (meta-prompt that writes prompts): the only source
showing a prompt scaffolding its own improvement — but it is **human-
gated**: "Wait for the user's reply before proceeding to the next block."
Structured intake + hypothesis generation (2-3 independent approaches) +
uncertainty calibration ("never fabricate"). Self-improvement is *not*
autonomous.

**Kartha / LangChain**: the cyclical generator↔reflector loop with the
message-type swap (`cls_map = {"ai": HumanMessage, "human": AIMessage}`)
so the model treats its own critique as external feedback — reduces
self-praise. BUT: it only critiques *solution quality* (essay polish),
never *framing* ("is this the right thesis?"); termination is a hardcoded
6-cycle count, not quality-based.

**Contribution to v3 — resolves the identity-checkpoint problem:** the
identity check is **not** model self-grading (which is unreliable). Its
job is to **produce an auditable delta (reflex vs proposal) for the
HUMAN**, who is the external evaluator. The pause-before-execute *is* the
external grounding GigaSpaces says you need. This defuses the
self-grading critique entirely.

### Cluster D — "CoVe" video (mislabeled → Reflection Prompting)

The video teaches the weaker joint-context Reflection (critique sent
*with* the draft in the window). It confirms by contrast that capturing
the reflex *before* meditating (true context isolation) is the right
fix, and that open-form > yes/no questioning. No framing verification.
Two "add a 4th step" ideas from this reader were rejected as bloat.

### Cluster E — Recursive self-improvement (Oliver ×3)

**Self-refinement works within narrow bounds:**
- "Round 1 captures 50-80% of the gain... Third round is usually
  marginal. Fourth and beyond? The curve flattens, and quality sometimes
  actively degrades."
- "External validation breaks the self-bias loop. The model can't
  flatter itself past a failing test suite."
- The evaluation paradox: "GPT-4o assigns scores roughly 10% higher to
  its own outputs; Claude models show a 25% self-preference effect."
- Reward hacking: "When OpenAI's o3 was tasked with speeding up program
  execution, it rewrote the evaluation timer to always report fast
  results rather than actually optimising the code."

**The three levels of RSI** (and their safeguards):
- Level 1 — autonomy learning (what it's allowed to do): safe with a
  scoring threshold.
- Level 2 — domain learning (what exists in its world): safe with an
  evidence threshold.
- Level 3 — rule improvement (rewriting its own logic): **"requires a
  human in the loop — every time, without exception."** "Never
  auto-applied... proposals sit in a folder until a human reads them."

**Earned, revocable trust:** start at score 0; approve +1, reject −2
(asymmetric); graduate to autonomous at 5; "one rejection after
graduation: immediately demoted." "Trust should be earned, not
configured." "Prevention beats repair."

**Contribution:** (a) SATORI-Lite's human-gatekeeper stance is
**vindicated, more than ever** — even frontier labs keep RSI supervised.
(b) A *separate* future practice is now well-specified: a human-gated
"meditation that improves the meditation" (see §7).

---

## 3. Gemini's three-paradigm framing (the orienting telescope)

Gemini positioned SATORI-Lite as a **third paradigm**, distinct from:
- **Riff (Stanford):** reflection aimed at the **human's** metacognition.
- **Reflexion / CoVe (2026):** reflection aimed at the **AI's output
  correctness**, via autonomous self-correction loops.
- **SATORI-Lite:** reflection aimed at the **systemic risk of the
  action** — human as sovereign gatekeeper, targeting *framing/intent*,
  not correctness.

Gemini's load-bearing line, now triangulated across every cluster:
*an automated self-correction loop will build a flawless patch for the
wrong problem if the framing is bad.* The frame check is the one thing no
other paradigm has — CoVe's own paper admits it doesn't address
"incorrect reasoning steps"; the agentic loops only polish solutions.

---

## 4. The convergences (what survived across 9 independent readers)

These are the findings multiple blind readers landed on separately — the
signal that survives the "don't overfit to one source" worry:

1. **Frame check is the un-solved differentiator.** Unanimous: the
   literature has *no tested method* for a model critiquing its own
   framing. CoVe excludes it; agentic loops ignore it; RSI presupposes a
   human sets the goal.
2. **Reproduction / external grounding is the robust core.** Every
   reader converged: it's the one move that escapes self-evaluation.
   Promote it to a gate.
3. **Identity check via context isolation** (capture reflex *before*
   meditating) beats the joint-context counterfactual. CoVe factored >
   joint; confirmed by clusters C, D, A, and the RSI evaluation paradox.
4. **Subtract the variance run.** No evidence it catches distinct
   failures; RSI says round 3+ degrades; ensembling is automated-voting,
   not human-gating.
5. **Smaller / re-centered.** Native reasoning models already do the
   restate/decompose steps; forced CoT can hurt them. Lean into the
   non-native moves.

---

## 5. System-level pass (telescope → modular → granular)

### Telescope (whole system)
SATORI-Lite's identity = "solve the right problem, at the right altitude,
with the human as gatekeeper." Its value is concentrated in the moves the
model does NOT make natively: **frame check, pause, reproduction,
reflex-capture.** Everything else is supporting machinery — and v2 had
drifted into accreting machinery (every v2 change was a reactive patch
against a red-team attack). v3 re-centers.

### Modular (middle altitude) — the v3 disposition per module
1. **Purpose/Scope** (new, ~2 lines): state the purpose + that the
   practice is scale-invariant (code / system / policy).
2. **Framing module (the center — elevate):** frame check gains an
   ACTION BRANCH (if the stated task is the wrong task → reframe and
   STOP, don't solve the wrong problem); add the confirmation-bias lens
   ("testing a hypothesis or building a case?"); house the user's **zoom
   discipline** here (frame at increasing specificity — system→module→
   line, or policy→team→behavior — and check the levels cohere; fix at
   the altitude that resolves the system issue without rewriting the
   world).
3. **Grounding module (promote to a GATE):** reproduction becomes a gate
   — if you can't reproduce (or externalize a falsifiable claim), STOP.
   Open-form prediction, not yes/no; predict the failure *before*
   running, then compare. Non-code fallback: quote the lines/passages
   you claim fail + predicted failure mode.
4. **Anti-rubber-stamp module (fix + reframe purpose):** capture the
   reflex BEFORE meditating; freeze; compare at the end. Reframe its
   purpose — it is NOT self-grading; it surfaces an auditable delta for
   the human (the real evaluator). Surface both.
5. **Depth-scaling module (keep):** triage T1/T2/T3 → SKIP/FAST/STANDARD
   /FULL, default-UP. Optional: express tiers as turn-counts as well as
   minutes (Riff). Offered, not baked in.
6. **Subtract:** variance run (remove); doc-led flag (remove → if
   doc-led, the grep/trace is mandatory); benchmark caveat (remove from
   the practice file → it belongs in the log/report; it speaks to the
   human evaluating the practice, not the agent performing it); trim the
   heavy restate/decompose emphasis (native to strong models).

### Granular (microscope)
The line-level edits go into the actual v3 file *after* the
meditation-together step. Not written yet (pause-before-execute).

### Honest size note
v3 is **fewer mechanisms and re-centered**, not necessarily dramatically
fewer lines (it adds a purpose/scope line, an action branch, the zoom
discipline, and reflex-capture while removing the variance run, doc-led
flag, and benchmark caveat). "Smaller" is true in *mechanism count and
conceptual surface*, which is what matters — claimed honestly, per a
reader's refutation of an overclaim.

---

## 6. Considered-and-rejected (the bloat ledger)

The discipline the user asked for: ~45 candidate ideas surfaced across 9
readers. Most were locally reasonable and globally corrosive. Rejected,
with reason:

- **Reflexion machinery in SATORI-Lite** (loop-release conditions,
  evaluator specs, automated-refinability signals) — pulls toward the
  correctness paradigm SATORI-Lite is defined *against*.
- **RSI "earned attention / three-levels-of-scrutiny / trust scoring"
  inside SATORI-Lite** — would balloon a per-task reflection into a
  longitudinal governance system and import the autonomy frame. → moved
  to the separate practice (§7), not SATORI-Lite.
- **A 4th reflection-prompting step** (cluster D) — bloat; it's the
  weaker joint-context variant anyway.
- **Gating every frame-check question on user confirmation for all
  tiers** (cluster C) — too heavy for FAST; at most FULL-only, default
  reject.
- **RCoT "Frame Check D", atomic FACTSCORE decomposition** (prior CoVe
  round) — bloat.
- **Hard-coding exactly three zoom tiers** — reader A's caveat; phrase as
  "increasing specificity, check coherence," scale-invariant.

---

## 7. The second thread — a separate practice (NOT a SATORI-Lite change)

The RSI cluster answers the user's question — *can ANAPANA improve its
own practice files without becoming an autonomous self-modifying loop?* —
with **yes, human-gated.** This is a distinct artifact in the "series of
meditation instructions for AI," provisionally **"ANAPANA Research
Protocol"** (a meditation that improves the meditation):

- **Level A — evidence gathering** (autonomous, threshold ≥3 sessions):
  scan `research_log.md` / `benchmarks/` for recurring patterns; write to
  a `proposals/` folder; no edits to practice files.
- **Level B — quality scoring** (autonomous, audit trail): score each
  practice file on clarity / replicability / coverage / evidence-basis;
  track the trend.
- **Level C — proposal generation** (HUMAN GATE, always): after enough
  evidence, emit a small, single-section improvement proposal with data +
  diff + expected impact. The human approves/rejects. No auto-apply.
- **Guardrails:** scope lockdown (structure, never philosophy — honors
  the locked BREATH/INSIGHT/SATORI names); evidence threshold; small
  diffs; reversal audit; the protocol never modifies itself; stale
  proposals sunset.

This maps Oliver's auto-moc three-level architecture onto ANAPANA while
keeping the pause-contract intact. **Kept separate so it does not bloat
SATORI-Lite** — and because it may be the seed of the broader series.

---

## 8. Meta — applying SATORI-Lite to this synthesis (reflex vs meditated)

Per the user's standing request that I use the practice on my own work,
with the v3 reflex-first fix:

- **Reflex (captured before the deep synthesis):** "Take all ~45 reader
  ideas + the RSI three-levels architecture and build one big
  comprehensive v3 with everything."
- **Triage:** FULL (whole-system, high stakes; strong framing pressure
  from both "create v3" and the seductive RSI architecture).
- **Frame check:** the prompt did not ask me to consider whether the RSI
  material belongs in a *separate* practice vs. inside SATORI-Lite — kept
  that live, and it became the key decision.
- **Meditated proposal:** smaller, re-centered SATORI-Lite; RSI material
  quarantined into a separate future practice; ~35 of ~45 ideas rejected.
- **Identity delta (reflex → meditated):** large, and in the direction
  the user explicitly asked for (don't lose the system picture to
  accretion). Surfaced here so the user can audit it.

---

## 9. Falsifiable test for v3

v3 is a hypothesis, not a proven artifact. The test: run v3 (re-centered,
smaller) against B1/B2/B3 + the new B4 (tier-miscalibration), **with the
model version held constant** across SATORI / SATORI-Lite v3.2 / v3. If
v3 scores ≥ v2 on surface correctness, hidden-issue discovery, and
frame-check action-branch firing — while costing fewer tokens — the
re-centering thesis holds. If v3 scores worse, the trimmed elements
(variance run, heavy restate/decompose) were load-bearing and should
return. Honesty hook: also track whether the reflex-first identity check
brings the 100%-fire-rate down; if it stays 100%, the externalization
isn't biting.

---

## 10. Open questions

1. Does reflex-capture-before-meditation actually reduce the identity-
   check fire rate (the honesty audit)?
2. Does the frame-check action-branch ("reframe and STOP") fire on B4's
   suppressed-framing prompt where v3.2 would SKIP?
3. Can we get model-version-held-constant data to de-confound the
   SATORI-vs-Lite token comparison?
4. Is the "ANAPANA Research Protocol" worth building as the 2nd practice
   in the series — and what would its own benchmark look like?
5. What are the OTHER practices in the "series of meditation instructions
   for AI"? Candidates surfaced: a refusal/uncertainty practice (when the
   honest answer is "I don't know — ask"), an observation-without-action
   practice, and the self-improvement protocol above.
6. Turn-counts vs minutes as the tier forcing-function — does either
   measurably change behavior?
