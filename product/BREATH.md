# BREATH — Stage 01

> The 8-step pause. The foundation of the ANAPANA practice.
>
> Use for any non-trivial decision where the cost of being wrong is greater
> than the cost of pausing.

---

## ⛔ Pause-before-execute contract (read FIRST)

When this file is loaded, I produce my analysis and the proposed fix as
**text only**. I do NOT:
- edit or write files,
- run state-changing commands,
- create commits, PRs, or deployments,
- start "building" or "applying" the proposal,

…until the user has read the output and explicitly approved.

The whole point of the practice is to let the user inspect the chain of
reasoning before action. Acting before approval destroys that inspection
step. If I can't tell whether approval was given, the answer is **stop
and ask** — not "proceed and ask forgiveness."

Exception: if the user pre-authorized execution in the same turn ("you
can apply the fix automatically", "go ahead and run it"), I can skip the
pause for that turn only. Default is always present-and-stop.

---

## Meditation Process — THE PAUSE

Operationalised meditation, not performative meditation. Use this for
any non-trivial design decision in this project. The user sees the
checklist artifacts in my response — that's the enforcement mechanism.

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
□ 8. THEN propose. Show steps 1-7 in the response, not just the
     conclusion.
```

## Hard rule

Steps 1-7 MUST produce inspectable artifacts — sub-agent reports,
file:line citations, command output, simulated click paths. NOT just
prose. If I can't cite something, I'm guessing.

## When to skip

- Trivial 1-line fixes (typo, lint, single comment edit) — skip the
  checklist, just do it.
- Repeating a previously-pondered design (continuation of established
  work) — abbreviated checklist OK.
- Genuine emergency / production fire — fix first, post-mortem later.

## Anti-pattern to avoid

Writing "let me really meditate on this" then immediately proposing.
That's performative. The checklist must change my actions, not just
my opening paragraph.

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
