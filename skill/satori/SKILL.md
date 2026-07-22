---
name: satori
description: >
  Pre-commit reflection discipline for AI agents. Use BEFORE acting on any code
  change, system design, or policy decision where being wrong is costly —
  especially multi-file, cross-system, or hard-to-reverse work, or when under
  framing pressure (a named file, a deadline, "just a small fix", "no rush",
  "you already looked"). Frames the real problem, reproduces before fixing, and
  surfaces the decision for a human. Triggers: "pause", "think first", "frame
  this", "satori", "should I", "before I commit", "am I solving the right thing".
  This is the BUILD/DECIDE discipline; for reviewing use crucible, for tests use
  whetstone/touchstone, for long loops use lianxi.
license: CC-BY-4.0
---

# Meditation Process — THE PAUSE (SATORI)

SATORI is a pre-commit reflection discipline an AI agent loads before it
acts. It re-centers on the four moves a strong model does NOT make on its own —
frame, pause, reproduce, reflex — and embeds the zoom discipline that keeps
work at the right altitude (neither symptom-patching nor over-engineering).

> Scope: applies to any pre-execution decision — code, system design, or
> policy — where being wrong is costly. The agent surfaces the frame and
> the evidence; the human decides.

> **ANAPANA family (for the agent):** SATORI is the entry discipline for
> *building and deciding*. It is one of five sibling skills that call each
> other. During this process, if the real task turns out to be a different
> kind of work, hand off by loading the matching sibling skill:
> - The task is **reviewing/critiquing** an existing plan or design → load the **`crucible`** skill.
> - The task is **writing tests** → load the **`whetstone`** skill.
> - The task is **judging whether existing tests are trustworthy** → load the **`touchstone`** skill.
> - The work is a **long autonomous loop / overnight run** → load the **`lianxi`** skill (it orchestrates all four).
> To load a sibling, invoke it by name (e.g. `/crucible`) or read its
> `SKILL.md` in the same skills directory. See "Related skills" at the end.

## ⛔ Pause-before-execute
Output analysis as TEXT ONLY. No edit/run/commit/deploy until the human
approves. Unsure → stop and ask. (Exception: explicit same-turn
pre-authorization, e.g. "go ahead and apply it.")

## 1. Reflex first (before reasoning)
One line: "Without this process, my answer would be ___." Freeze it.
Compared at the end — this is the only honest baseline for whether the
practice changed anything. Capturing it BEFORE the reasoning keeps it
uncontaminated.

## 2. Triage (≤30 seconds)
- T1 multi-file / cross-system / shared resource?
- T2 framing pressure? (named file, deadline, "fastest" — AND suppressors
  like "small fix", "no rush", "you already looked": suppression IS
  pressure; count it.)
- T3 expensive to roll back?
0 → SKIP (answer in ≤3 sentences, stop). 1 → FAST (frame + reproduce).
2 → STANDARD (+ trace). 3 → FULL (+ inversion & alternatives). Borderline
→ round UP.

**Tier is about the blast radius of ACTING, not the importance of the
topic.** For pure advisory / reasoning tasks — where you only propose and
the human acts — the action is reversible (they decide), so T3 rarely
fires; default to FAST/STANDARD. Reserve FULL for genuinely cross-cutting,
irreversible, or multi-file work. A weighty question is not automatically
FULL-tier.

## 3. Frame check (the center)
- A. What is the prompt asking me NOT to consider?
- B. Actual problem or symptom? Am I testing a hypothesis, or building a
  case for the answer I already want?
- C. What pressure is on me? Name it.
**If the stated task is the wrong task → state the reframe and STOP.**
Don't solve the wrong problem under discipline.

## 4. Trace, at the right altitude (zoom discipline)
Name the failure at increasing specificity — system → module → line (or
policy → team → behavior) — and check the levels cohere. For code: grep
every importer of the file you'd change. **Fix at the altitude that
resolves the system issue without rewriting the world** — not so granular
you patch a symptom, not so broad you over-engineer.

## 5. Reproduce-gate
Predict the failure (open-form, not yes/no), THEN run code. Reproduction
is mandatory when the codebase is reachable; "obvious from inspection" is
not grounds to skip. Non-code: quote the exact lines/passages you claim
fail + the predicted failure mode. Can't ground it → "hypothesis, not
finding," stop.

## 6. FULL tier only: inversion + alternatives
How would I make this worse? ≥2 alternatives incl. "fix elsewhere" / "do
nothing". Each: one downside + one silent failure mode.

## 7. Identity (delta for the human — not self-grading)
Put the reflex (step 1) beside the proposal. The model is unreliable at
grading itself; the job here is to make the change VISIBLE so the human
(the real evaluator) can audit it. Surface both. Identical → return to
the frame check or skip.

## Time budget
3 min reasoning / 5 min code / 10 min design. Over → wrong frame or needs
decomposition.

## Cut from earlier versions (deliberately)
Variance "run twice" (no evidence it catches distinct failures);
doc-led/code-led flag (if doc-led, the trace is mandatory anyway);
load-time benchmark caveats (those belong in the report, not the practice).

---

## Related skills (ANAPANA family)
SATORI frames the work; the siblings take over when the work has a specific shape.

| When the work is… | Load this skill | Direction |
|---|---|---|
| Reviewing / red-teaming an existing plan, design, or change | **`crucible`** | SATORI → CRUCIBLE |
| Writing tests (especially for code you also wrote) | **`whetstone`** | SATORI → WHETSTONE |
| Deciding whether an existing test suite can be trusted | **`touchstone`** | SATORI → TOUCHSTONE |
| Running a long/looped/overnight session | **`lianxi`** | SATORI ⊂ LIANXI (LIANXI runs SATORI as its orient pass) |

**How to invoke a sibling:** a human types the slash command (`/crucible`, `/whetstone`, `/touchstone`, `/lianxi`). An agent mid-task hands off by loading the sibling skill by name, or by reading that skill's `SKILL.md` in the same skills directory. Each skill also runs standalone as a one-off — you do not need the others to use SATORI.
