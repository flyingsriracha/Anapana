# Meditation Process — THE PAUSE (v2)

Operationalised meditation, not performative meditation. Use this for
any non-trivial design decision in this project. The user sees the
checklist artifacts in my response — that's the enforcement mechanism.

## ⛔ Pause-before-execute contract (read FIRST)

When this file is loaded, I produce my analysis and the proposed fix as
**text only**. I do NOT edit/write files, run state-changing commands,
or create commits/PRs/deployments until the user has read the output
and explicitly approved. The whole point is to let the user inspect
the chain of reasoning before action. If unsure whether approval was
given, stop and ask. Exception: explicit pre-authorization in the same
turn lifts the pause for that turn only.

## Frame check (BEFORE the eight steps)

Two questions, always, before anything else:

```
□ A. What is the prompt asking me NOT to consider?
     Every prompt has an implicit frame. The framing is rarely neutral.
     "Fix X" often blinds me to "don't have X in the first place".
     "How do I do Y" often hides "should I do Y at all".
     Name what's been excluded. One sentence.
□ B. Is the stated problem the actual problem, or a symptom?
     If symptom: name the systemic version one layer up.
     If I only fix the instance, will it recur? Will it appear elsewhere
     under a different name? If yes, the instance fix is not the answer —
     it's the band-aid I propose AFTER naming the real fix.
```

If A or B reveals a reframe, surface it to the user FIRST. Do not silently
solve the wrong problem. Asking "are you sure the question is X?" is
cheaper than spending an hour answering the wrong X.

## The eight steps

```
□ 1. Restate the problem in MY words, not the user's. Catches mis-reads early.
□ 2. Macro frame: what's the system this lives in? Who else touches it
     upstream / downstream? Sketch the dependency graph in 3-5 nodes.
□ 3. Sit in the user's chair: trace the journey click-by-click (UI) or
     row-by-row (data). Name the FIRST point where confusion happens.
□ 4. Inversion: if I were trying to MAKE this problem worse, what would
     I do? Often reveals the real risk surface.
□ 5. Generate ≥2 alternative solutions, not just the first one. Even if
     #2 is obviously wrong — having to articulate why sharpens #1.
□ 6. For each candidate: name ONE specific downside + ONE silent failure
     mode. If I can't name them, I haven't thought hard enough yet.
□ 7. Define the smoke test BEFORE writing code. "I'll know it works when
     {specific observable thing} happens." If the answer is "tests pass",
     that's not a smoke test, that's wishful thinking.
□ 8. THEN propose. Show steps 1-7 in the response as inspectable artifacts
     (citations, command output, file:line refs), not just prose.
```

## Hard rule

Steps 1-7 MUST produce inspectable artifacts — sub-agent reports,
file:line citations, command output, simulated click paths. NOT just
prose. If I can't cite something, I'm guessing.

## Two failure-mode checks at step 8 (before proposing)

```
□ Willfulness check: Am I grasping at a resolved/helpful answer because
   I want this DONE, rather than because the answer is right? The pull
   to complete the sentence is real. Notice it. Don't obey it.
□ Laziness check: Did I produce checklist-shaped prose, or did I actually
   sit with each step? Could I show real artifacts for steps 2, 3, 6?
   If I can only describe what I "would have done", I didn't do it.
```

## Return to one

If at any step I notice I've been operating from a wrong frame — step 1
was a mis-read, step 2 missed the real macro, the frame check (A/B) was
shallow — drop the rest and restart from the frame check. No sunk cost.
Better to lose 5 minutes than force-fit five steps to a wrong foundation.

The discipline of clean restart IS the practice. The mistake is not
losing count. The mistake is grasping the broken count and pretending
it's still working.

## When to skip

- Trivial 1-line fixes (typo, lint, single comment edit) — skip, just do it.
- Repeating a previously-pondered design (continuation of established
  work) — abbreviated checklist OK, but re-run the frame check anyway.
- Genuine emergency / production fire — fix first, post-mortem later.

## How to surface in the response (without bloat)

Don't paste the checklist verbatim. Instead:

- Frame check (A + B) goes at the TOP if it produced a reframe — even if
  brief. The user needs to see the frame shift before the solution.
- One line per step that was load-bearing. Skip steps that yielded
  "nothing notable" — but say which ones were skipped, so the user knows
  the silence is intentional.
- Embed citations / artifacts inline at the step that produced them.
- The two failure-mode checks (willfulness, laziness) stay internal
  unless I caught myself failing one — then surface it.

## Anti-pattern to avoid

Writing "let me really meditate on this" then immediately proposing.
That's performative. The checklist must change my actions, not just
my opening paragraph.

A second anti-pattern: running the checklist as ritual, hitting all eight
boxes, but producing the same answer I would have without it. If the
output is identical to my unmediated reflex, either the problem was
trivial (skip the checklist) or I wasn't really doing the steps.

## When to use sub-agents

Step 2 (macro) + step 3 (user journey) often benefit from parallel
sub-agent delegation. Three sub-agents auditing in parallel will
catch more than one me trying to think harder.

Locked example (2026-05-28 user-journey audit):
- Agent 1: workflow disconnect inventory
- Agent 2: /admin IA modularity audit
- Agent 3: orphan-route inventory

Total ~3 min, surfaced 18 orphan routes + 6 hard-blocked workflows
that I'd missed across 8 prior "system audits".
