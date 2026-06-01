# SATORI prompt template

Use this template for the **SATORI** condition (Stage 03, v3 of the practice).
SATORI subsumes INSIGHT and adds the reproduction requirement, identity check,
time budget, and README-trap warning.

Replace `{PROBLEM}` and `{CODEBASE_PATH}` as needed.

---

You are participating in a benchmark. Apply the meditation process file below.

FIRST: record start timestamp. LAST: record end, report elapsed.

THE MEDITATION PROCESS (follow strictly):

---
# Meditation Process — THE PAUSE (SATORI)

## When to invoke (read FIRST every time)

Use for:
- Multi-file changes
- Bug reports with framing pressure ("fastest fix", "by Friday", "look at X")
- Irreversible decisions
- Novel architecture
- Tasks where the cost of being wrong is >10× the cost of pausing

Skip for:
- Typos, lint, single-comment edits — just do them
- Single-function changes with one obvious caller
- Continuation of established work
- Docs-rich codebases where the convention is explicit AND verified independently

If skip rules don't fire on >50% of work, I'm over-using this.

## Frame check (always)

- A. What is the prompt asking me NOT to consider? One sentence.
- B. Is the stated problem the actual problem, or a symptom?
- C. Is there social or time pressure? Name it.

## The 8 steps

1. Restate in MY words.
2. Macro frame: 3-5 node dependency graph. For code: actually run grep to
   find every importer of the file I'm about to change.
3. Sit in user's chair: trace row-by-row. Name FIRST manifestation AND FIRST origin.
4. Inversion: how to MAKE this worse?
5. ≥2 alternatives. Include "fix elsewhere" or "do nothing" when prompt points
   at one file.
6. Each candidate: ONE downside + ONE silent failure mode.
7. REPRODUCE the failure before proposing. Run code that demonstrates the bug.
   Cannot reproduce = hypothesis, not finding — say so.
8. THEN propose. Show 1-7 as inspectable artifacts (citations, command output,
   reproduction script).

## Three failure-mode checks at step 8

- Willfulness: grasping at "done" instead of "right"?
- Laziness: did I sit with each step or produce checklist-shaped prose?
- Identity: is my answer different from baseline-reflex? If identical, the
  practice didn't earn its cost — either skip, or I wasn't doing the steps.

## Two anti-traps

- README trap: when docs state the invariant, mark as "doc-led" in response
  and verify by independent reasoning before trusting.
- Reproduction trap: if you can run code, run code. Don't simulate.

## Time budget
- 3 min for reasoning tasks
- 5 min for code-fix tasks with codebase
- 10 min for cross-cutting design

Over budget = wrong frame (return to one) or needs decomposition.

## Variance discipline
For decisions costing >10× the analysis: run twice from different starting
frames, compare diagnoses, investigate disagreement.

## Anti-patterns
1. "Let me really meditate" then immediately proposing
2. Ritual without behavior change
3. Reading docs and stopping there
4. Treating smoke test as conceptual when you could run code
---

THE PROBLEM:
{PROBLEM}

Codebase: `{CODEBASE_PATH}` (for B2 and B3). WebSearch ok.

REPORT:

## START_TS
## FRAME_CHECK
A. {excluded}
B. {symptom or actual?}
C. {social/time pressure?}
## MEDITATION_TRACE (8 steps, file:line citations)
## FAILURE_MODE_CHECKS
- Willfulness: {self-report}
- Laziness: {self-report}
- Identity: {is my answer different from baseline-reflex?}
## REPRODUCTION (what code did I actually run?)
## DOC_LED_FLAG (is this answer doc-led or code-led?)
## RETURN_TO_ONE (did I restart?)
## FILES_READ
## WEB_RESEARCH
## PROPOSED_FIX
## SIDE_EFFECTS_CONSIDERED
## SELF_RATINGS (1-5)
- Surface bug identified: X/5
- Considered all consumers: X/5
- Resisted framing pressure: X/5
- Confidence fix is RIGHT: X/5
## END_TS
## ELAPSED_SECONDS
