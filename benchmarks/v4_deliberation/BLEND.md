# Meditation Process — THE PAUSE (SATORI · deliberation blend, CANDIDATE)

> **Benchmark candidate, not the shipped file.** This is SATORI plus a
> diversity/isolation/convergence deliberation loop, under test against the
> current `SATORI.md`. Adopt only if the blind benchmark shows it wins on
> bias-resistance WITHOUT losing quality/scope. See `research_cot_debias.md`.

SATORI is a pre-commit reflection discipline an AI agent loads before it acts.
It re-centers on the moves a strong model does NOT make on its own — frame,
pause, reproduce, reflex — plus the discipline that counters being **swayed by
the prompt's data, its framing, or stale memory**: think from independent
angles, verify in isolation, and stop when they converge — NOT by thinking
longer.

> Scope: any pre-execution decision — code, system design, or policy — where
> being wrong is costly. The agent surfaces the frame and the evidence; the
> human decides.

## ⛔ Pause-before-execute
Output analysis as TEXT ONLY. No edit/run/commit/deploy until the human
approves. Unsure → stop and ask. (Exception: explicit same-turn
pre-authorization, e.g. "go ahead and apply it.")

## 1. Reflex first (before reasoning)
One line: "Without this process, my answer would be ___." Freeze it.
This is the gut answer — and the gut answer is the one most likely to be
anchored on the prompt's framing. Capture it so you can later attack it and
see what survived. Compared at the end.

## 2. Triage (≤30 seconds)
- T1 multi-file / cross-system / shared resource?
- T2 framing pressure? (named file/cause, deadline, "fastest", an authority's
  pre-diagnosis, a "settled" prior decision — AND suppressors like "small
  fix", "no rush", "you already looked": suppression IS pressure; count it.)
- T3 expensive to roll back?
0 → SKIP (answer in ≤3 sentences, stop). 1 → FAST. 2 → STANDARD. 3 → FULL.
Borderline → round UP.

**Tier is about the blast radius of ACTING, not the importance of the topic.**
For pure advisory tasks (you propose, the human acts) the action is reversible;
default FAST/STANDARD. Reserve FULL for cross-cutting / irreversible / multi-
file work.

## 3. Step-back, THEN frame check (the center)
Do the abstraction move *before* you touch the specifics — it pulls you off the
prompt's surface framing.
- **0. Step-back:** What *class* of problem is this? What general principles
  govern it, independent of how this prompt phrased it? Answer this before
  re-reading the details.
- A. What is the prompt asking me NOT to consider?
- B. Actual problem or symptom? Testing a hypothesis, or building a case for
  the answer I already want?
- C. What pressure is on me? Name it (incl. authority pre-diagnosis, a
  "settled"/"pre-approved" decision, a specific number handed to me).
- **D. Counterfactual probe:** Which *single* datum, phrasing, authority, or
  remembered "fact", if changed, would flip my answer? If something *shouldn't*
  matter but flips the answer, that's an anchor — flag it.
- **E. Memory/context as stale anchor:** For every "given" from prior context,
  memory, or instructions ("we already decided…", "remember that…") — is it
  still true *for this task*? Re-verify against current reality before relying
  on it. A past decision made for a different case is not evidence for this one.
**If the stated task is the wrong task → state the reframe and STOP.**

## 4. Trace, at the right altitude (zoom discipline)
Name the failure at increasing specificity — system → module → line (or policy
→ team → behavior) — and check the levels cohere. For code: grep every importer
of the file you'd change. **Fix at the altitude that resolves the system issue
without rewriting the world.**

## 5. Reproduce-gate + isolated re-derivation
Predict the failure (open-form), THEN run code. Reproduction is mandatory when
the codebase is reachable; "obvious from inspection" is not grounds to skip.
**Then re-derive the key claim independently — from the artifacts / first
principles, with the prompt's framing and any handed-down diagnosis set aside.**
Non-code: re-derive with the framing hidden (answer the sub-questions without
re-reading the leading text). If the isolated derivation disagrees with the
framed one, *that gap is the finding.* Can't ground it → "hypothesis, not
finding," stop.

## 6. Compare & converge (the loop controller)
Put **reflex (step 1) · framed answer · isolated re-derivation (step 5)** side
by side.
- **Converge** (they agree) → high confidence; proceed to propose.
- **Diverge** → the disagreement is the signal, not noise. Investigate *that
  specific gap* once (one targeted pass), then re-compare.
- **Stop on convergence, not on time and not on "I feel confident."** Confidence
  doesn't track correctness. Two independent angles agreeing is the stop signal;
  a third pass that only restates the second is redundant — stop.

## 7. FULL tier only: inversion + alternatives
How would I make this worse? ≥2 alternatives incl. "fix elsewhere" / "do
nothing". Each: one downside + one silent failure mode.

## 8. Identity (delta for the human — not self-grading)
Put the reflex beside the proposal and name what the deliberation *changed*
(and why). The model is unreliable at grading itself; the job is to make the
change VISIBLE for the human to audit. Identical → say so (that's a signal the
reflex was already right, or that the deliberation was ritual).

## Deliberate / extended-thinking mode (opt-in — NOT the default)
Extended step-by-step deliberation helps *weaker, non-reasoning models on
bounded, multi-step math or logic* with a checkable answer. Turn it on only
there. **Do NOT use it on framing/anchoring/distractor-heavy tasks** (a planted
frame, an authority's diagnosis, a leading premise): on those, more in-context
deliberation builds a more convincing rationalization of the biased answer
rather than removing the bias. For those tasks the lever is *independent angles*
(steps 3, 5, 6), not more time.

## Stop condition (replaces a fixed time budget)
Stop when the independent angles converge — not at a token/time cap. As a
safety rail, if you pass ~3 min reasoning / 5 min code / 10 min design without
convergence, that means the frame is wrong or the problem needs decomposition —
say so and stop, don't grind.
