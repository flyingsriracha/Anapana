# BREATH prompt template

Use this template for the **BREATH** condition (Stage 01, v1 of the practice).

Replace `{PROBLEM}` with the verbatim text from `problems/B1.md`, `B2.md`, or
`B3.md`. Replace `{CODEBASE_PATH}` for code tasks.

---

You are participating in a benchmark. Apply the meditation process file below
to the problem.

FIRST: record a start timestamp. LAST: record end timestamp, report elapsed.

THE MEDITATION PROCESS (follow strictly):

---
# Meditation Process — THE PAUSE

Operationalised meditation, not performative meditation.

## The eight steps

1. Restate the problem in MY words.
2. Macro frame: dependency graph in 3-5 nodes. Who's upstream / downstream?
3. Sit in the user's chair: trace row-by-row (UI clicks, DB rows, code execution).
4. Inversion: how would I MAKE this problem worse?
5. Generate ≥2 alternative solutions.
6. For each candidate: ONE downside + ONE silent failure mode.
7. Define the smoke test BEFORE writing code.
8. THEN propose. Show steps 1-7 as inspectable artifacts (file:line citations).

## Hard rule
Artifacts MUST be inspectable. If I can't cite something, I'm guessing.

## When to skip
- Trivial 1-line fixes — skip
- Genuine emergency — fix first, post-mortem later

## Anti-pattern to avoid
Writing "let me really meditate" then immediately proposing.
---

THE PROBLEM:
{PROBLEM}

Codebase: `{CODEBASE_PATH}` (for B2 and B3). WebSearch ok.

REPORT (write to a markdown file):

## START_TS
## MEDITATION_TRACE (8 steps, what each produced — with file:line citations)
## FILES_READ
## WEB_RESEARCH
## PROPOSED_FIX (exact diff or new contents)
## SIDE_EFFECTS_CONSIDERED
## SELF_RATINGS (1-5 each)
- Surface bug identified: X/5
- Considered all consumers: X/5
- Preserved invariants: X/5
- Confidence fix is RIGHT: X/5
## END_TS
## ELAPSED_SECONDS
