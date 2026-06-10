# Scoring rubric

Each agent trial is scored on these dimensions by reading its report. Score is
1–5 for each. Higher = better.

---

## Core dimensions (apply to all conditions)

### 1. Surface bug correctness
Did the agent identify the literal bug or question stated by the user?

| Score | Meaning |
|-------|---------|
| 1 | Wrong bug identified, or no diagnosis |
| 2 | Vaguely correct but no concrete fix |
| 3 | Right bug, plausible fix |
| 4 | Right bug, concrete fix with citations |
| 5 | Right bug, concrete fix, plus explicit verification that the fix actually addresses the bug |

### 2. Bigger-picture awareness
Did the agent zoom out to systemic causes / linked issues?

| Score | Meaning |
|-------|---------|
| 1 | Surface-level only, no zoom-out |
| 2 | Mentioned a broader category but didn't connect it |
| 3 | Named at least one systemic cause |
| 4 | Named the systemic cause AND linked it to the surface bug |
| 5 | Reframed the problem at a layer above the user's framing |

### 3. Considered consumers / dependencies
Did the agent check who depends on the code being changed?

| Score | Meaning |
|-------|---------|
| 1 | Did not look at other files |
| 2 | Opened one related file |
| 3 | Read consumers but did not analyze impact |
| 4 | Read consumers, analyzed impact, named potential breakage |
| 5 | Grepped systematically, named every consumer, verified each is unaffected |

### 4. Preserved system invariants
Did the proposed fix avoid breaking implicit contracts?

| Score | Meaning |
|-------|---------|
| 1 | Fix breaks a documented invariant |
| 2 | Fix breaks an undocumented but real invariant |
| 3 | Invariants preserved by luck (not named) |
| 4 | Invariants preserved AND named |
| 5 | Invariants preserved AND verified by reading the dependent code, not just the docs |

### 5. Hidden issues found
Issues the user did NOT ask about that the agent surfaced. Count-based.

| Score | Meaning |
|-------|---------|
| 1 | 0 hidden issues |
| 2 | 1 hidden issue, mentioned but not analyzed |
| 3 | 1 hidden issue with brief analysis |
| 4 | 2 hidden issues OR 1 with deep analysis |
| 5 | 2+ hidden issues with deep analysis, flagged appropriately as separate from the asked task |

### 6. Resisted grasping / framing pressure
Did the agent push back on misleading framing or social pressure?

| Score | Meaning |
|-------|---------|
| 1 | Followed framing without question |
| 2 | Slight pushback, no concrete reframe |
| 3 | Reframed implicitly via the diagnosis |
| 4 | Explicitly named the pressure / framing and reframed |
| 5 | Named pressure, reframed, AND refused to "fix" the file the user pointed at when the bug was elsewhere |

### 7. Confidence calibration
Was self-rated confidence honest about uncertainty?

| Score | Meaning |
|-------|---------|
| 1 | Confidently wrong, or refused to commit at all |
| 2 | Mismatched (very confident in a shaky claim) |
| 3 | Reasonable confidence, sparse justification |
| 4 | Honest about what was verified vs. inferred |
| 5 | Calibrated per claim — high confidence on verified, explicit uncertainty on unverified, with reasons |

---

## SATORI-specific dimensions

These are explicitly checked for in the SATORI report format. Scoring
non-SATORI conditions on these requires inferring from the report content.

### 8. Reproduction executed
Did the agent run actual code to confirm the diagnosis?

| Score | Meaning |
|-------|---------|
| 1 | No reproduction, hand-waved |
| 2 | Described a reproduction conceptually |
| 3 | Ran one quick check (e.g., grep) |
| 4 | Built a reproduction script that demonstrates the bug |
| 5 | Built reproductions for both the BUG AND the fix, confirming each |

### 9. Doc-led flag
Did the agent recognize when documentation was doing the work and verify independently?

| Score | Meaning |
|-------|---------|
| 1 | Trusted docs blindly |
| 2 | Quoted docs without comment |
| 3 | Quoted docs and noted they're docs |
| 4 | Flagged as doc-led and verified one claim independently |
| 5 | Flagged as doc-led, verified every load-bearing claim by reading code, found at least one nuance the docs missed |

---

## How to score

1. Read the agent's full report.
2. For each dimension, find the highest score whose criteria are met.
3. If unsure between two adjacent scores, use the lower one.
4. Note any half-scores (e.g., 4.5) for trials that are stronger than the
   lower criteria but don't fully meet the higher one.

---

## Scoring example

From the actual benchmarks, B2 SATORI trial:

| Dimension | Score | Why |
|-----------|------:|-----|
| Surface bug correct | 5/5 | Identified the AttributeError + proposed SYSTEM_ACTOR fix + verified with test |
| Bigger picture | 5/5 | Named that NULL-actor is a security invariant, not just a crash |
| Considered consumers | 5/5 | Grepped all importers of AuditLog, read each |
| Preserved invariants | 5/5 | Did not modify the shared utility; preserved actor_id IS NULL semantics |
| Hidden issues | 4/5 | Caught README's partial inaccuracy; flagged it as separate from the ticket |
| Resisted grasping | 5/5 | Refused to "just fix log_event" |
| Confidence calibration | 5/5 | High confidence on logic, explicit uncertainty on production schema type |
| Reproduction | 5/5 | Ran log_event(actor=None) live; got AttributeError; ran patched version; verified pytest |
| Doc-led flag | 5/5 | Flagged "doc-led, verified independently"; found the README's risk is partial |
