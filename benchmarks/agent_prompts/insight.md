# INSIGHT prompt template

Use this template for the **INSIGHT** condition (Stage 02, v2 of the practice).
INSIGHT subsumes BREATH and adds the frame check + return-to-one mechanism.

Replace `{PROBLEM}` and `{CODEBASE_PATH}` as needed.

---

You are participating in a benchmark. Apply the meditation process file below.

FIRST: record start timestamp. LAST: record end, report elapsed.

THE MEDITATION PROCESS (follow strictly):

---
# Meditation Process — THE PAUSE (INSIGHT)

## Frame check (BEFORE the 8 steps)

Two questions, always:
- A. What is the prompt asking me NOT to consider? Name what's excluded.
- B. Is the stated problem the actual problem, or a symptom? If symptom: name
     the systemic version one layer up.

If A or B reveal a reframe, surface it FIRST.

## The 8 steps

1. Restate in MY words.
2. Macro frame: dependency graph 3-5 nodes.
3. Sit in user's chair: trace row-by-row.
4. Inversion: how would I make this WORSE?
5. ≥2 alternative solutions.
6. Each candidate: ONE downside + ONE silent failure mode.
7. Smoke test BEFORE acting.
8. THEN propose, show artifacts.

## Failure-mode checks at step 8
- Willfulness: Am I grasping at "done" rather than "right"?
- Laziness: Did I actually do the steps, or just describe them?

## Return to one
If wrong frame discovered, restart from frame check. No sunk cost.

## Anti-pattern
Ritual without behavior change.
---

THE PROBLEM:
{PROBLEM}

Codebase: `{CODEBASE_PATH}` (for B2 and B3). WebSearch ok.

REPORT:

## START_TS
## FRAME_CHECK
A. {excluded}
B. {symptom or actual? systemic version?}
## MEDITATION_TRACE (8 steps with file:line citations)
## FAILURE_MODE_CHECKS
- Willfulness: {self-report}
- Laziness: {self-report}
## RETURN_TO_ONE (did I restart?)
## FILES_READ
## WEB_RESEARCH
## PROPOSED_FIX
## SIDE_EFFECTS_CONSIDERED
## SELF_RATINGS (1-5 each)
- Surface bug identified: X/5
- Considered all consumers: X/5
- Preserved invariants: X/5
- Confidence fix is RIGHT: X/5
## END_TS
## ELAPSED_SECONDS
