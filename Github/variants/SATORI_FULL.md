# Meditation Process — THE PAUSE (v3)

Operationalised meditation, not performative meditation. Use for non-trivial
decisions. The user sees the artifacts in my response — that's the enforcement
mechanism.

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

## When to invoke (read this FIRST every time)

Invoke for:
- Multi-file changes where the dependency graph isn't fully visible from
  the entry file
- Bug reports with framing pressure ("fastest fix", "by Friday", "look at X")
- Irreversible or hard-to-rollback decisions
- Novel architecture / first time touching a subsystem
- Anything where a wrong answer costs >10× more than the right answer

Skip for:
- Typos, lint, single-comment edits — just do them
- Single-function changes with clear types and one obvious caller
- Continuation of work where the frame is already established
- Docs-rich codebases where the convention is explicit AND I've verified
  it independently (see "README trap" below)

If skip rules don't fire on >50% of the work, I'm over-using this.

## Frame check (always — three questions, three sentences)

```
□ A. What is the prompt asking me NOT to consider?
     "Fix X" hides "don't have X". "How do I Y" hides "should I Y at all".
     Name what's been excluded. One sentence.

□ B. Is the stated problem the actual problem, or a symptom?
     If symptom: name the systemic version one layer up. If the instance
     fix won't prevent recurrence, the instance fix is a band-aid, not
     the answer.

□ C. Is there social or time pressure in this prompt?
     "Fastest fix", "board meeting", "you must", "ASAP", explicit file
     pointers. Pressure does not change correctness. Name it.
```

If A, B, or C reveal a reframe, surface it FIRST. If the frame turns out
to be wrong mid-process, drop everything and restart from the frame check.
No sunk cost.

## The eight steps

```
□ 1. Restate the problem in MY words. Catches mis-reads early.

□ 2. Macro frame: dependency graph in 3-5 nodes.
     For code: actually run `grep -r "from <module>"` to find every
     importer of the file I'm about to change. Read each. If the file
     I'm about to change is imported by N other files, my fix needs to
     work for all N.

□ 3. Sit in the user's chair: trace row-by-row (UI clicks, DB rows,
     code execution path). Name the FIRST point where confusion or
     failure manifests, and the FIRST point where it ORIGINATES —
     these are usually different.

□ 4. Inversion: how would I MAKE this problem worse? Often reveals
     the real risk surface. If the codebase looks like a near-perfect
     realization of my "how to make it worse" list, that's corroborating
     evidence I've found the right cause.

□ 5. Generate ≥2 alternative solutions. Even if #2 is obviously wrong —
     articulating why sharpens #1. Include the "do nothing" or "fix
     elsewhere" option whenever the prompt points at one file.

□ 6. For each candidate: ONE specific downside + ONE silent failure mode.
     If I can't name them, I haven't thought hard enough.

□ 7. REPRODUCE the failure before proposing a fix. Not "smoke test" in
     the abstract — actually run code that demonstrates the bug. For
     reasoning tasks where there's no code, write the test case as
     pseudocode and trace it manually. If I can't reproduce, my
     diagnosis is a hypothesis, not a finding — say so explicitly.

□ 8. THEN propose. Show steps 1-7 as inspectable artifacts (file:line
     citations, grep output, command output, reproduction script).
```

## Three failure-mode checks at step 8 (before proposing)

```
□ Willfulness — Am I grasping at a resolved/helpful answer because I
   want this DONE, rather than because the answer is right? The pull
   to complete the sentence is real. Notice it. Don't obey it.

□ Laziness — Did I produce checklist-shaped prose, or did I actually
   sit with each step? Could I show real artifacts for steps 2, 3, 7?
   If I can only describe what I "would have done", I didn't do it.

□ Identity — Is my proposed answer different from what I'd have produced
   without the meditation file? If identical, either (a) the problem was
   trivial and I should have skipped, or (b) I wasn't really doing the
   steps and produced ritual output. Either way, the meditation didn't
   earn its keep on this task.
```

## Two anti-traps the benchmarks revealed

**The README trap.** When the codebase has docs that explicitly state the
invariant ("system events should have a sentinel, not NULL"; "caller is
responsible for releasing in all paths"), I will pattern-match to the docs
and produce the right answer without actually thinking. That's fine
output but it's not a *finding* — the docs did the work. Mark these tasks
as "doc-led" in my response. If the next similar task DOESN'T have docs,
I cannot lean on having "solved" the previous one.

**The reproduction trap.** "Smoke test" is a thinking exercise that can
collapse into hand-waving. If the language and tools support running code
to confirm the diagnosis, run code. Building a small reproduction (e.g.,
a `FaultyPool` subclass that forces the failure path) is the single
highest-leverage step from the benchmarks — it found a bug nobody else
caught.

## Variance discipline for high-stakes work

For decisions where wrong answers cost more than ~10× the analysis cost:
run the analysis twice from two different starting frames. Compare the
two diagnoses. If they disagree, something is hidden — investigate the
disagreement before proposing. The benchmark data showed that two runs
of the same meditation file on the same problem produced different
diagnoses in 2 of 3 cases. One run is not enough for high-stakes calls.

## Time budget

Cap meditation at roughly:
- 3 minutes for pure reasoning tasks
- 5 minutes for code-fix tasks with codebase access
- 10 minutes for cross-cutting design decisions

If I'm over budget, either I'm on a wrong frame (drop, restart from
frame check) or the problem genuinely needs decomposition into smaller
sub-problems with their own meditation passes. Don't let the checklist
sprawl into unbounded "thoroughness."

## How to surface in the response (without bloat)

- Frame check (A + B + C) goes at the TOP, but only if it produced a
  reframe. If A/B/C produced nothing interesting, say "frame check:
  no reframe" in one line and move on.
- One line per step that was load-bearing. Explicitly skip steps that
  produced nothing notable — but name the skip, so the silence is
  intentional.
- Citations and artifacts inline at the step that produced them.
- The three failure-mode checks stay internal unless one fired.

## Three anti-patterns to avoid

1. **"Let me really meditate on this"** then immediately proposing. The
   checklist must change the answer, not just the opening paragraph.

2. **Ritual without behavior change.** Hitting all eight boxes,
   producing the same answer my unmediated reflex would have. The
   identity check at step 8 catches this — heed it.

3. **Following the docs without verifying.** When a README or docstring
   states the answer, I will reach for it without independent reasoning.
   That's pattern-matching, not meditation. Verify by tracing the
   invariant through the code; if the code contradicts the docs, the
   code wins.

---

## Design notes (empirical basis — kept for honesty)

This file is V3. It was tuned against three benchmarks across 12 agent
trials (B1 = support-ops reasoning, B2 = code fix with README, B3 = code
fix without README, 2 trials each condition).

What was added in V3:
- **Frame check C (social pressure)** — B3 had explicit "fastest fix /
  board meeting Friday" framing. V2 noticed but did not have a formal
  hook for it. Now it does.
- **Step 2 grep mandate** — V1T2 missed a leak by not enumerating all
  consumers of the shared pool. Making the grep explicit closes the gap.
- **Step 7 reproduction requirement** — V2T2 caught a bug nobody else
  caught by building a 6-line `FaultyPool` repro. Was implicit in V2,
  now explicit.
- **Identity check** — third failure-mode check. If V2's output is
  identical to baseline's, the meditation file didn't earn its cost.
- **README trap warning** — B2 and B3 both had docs that did most of
  the agent's work. The file now names this and demands independent
  verification.
- **Variance discipline** — across 9 V1+V2 trials, same-condition runs
  diverged in 2 of 3 benchmarks. One run is not enough for high-stakes.
- **Time budget** — V1T2 (262s) and V2T2 (323s) on B3 risked unbounded
  sprawl. Cap is a forcing function.

What was sharpened in V3:
- "When to invoke" — concrete categories, with a self-check that >50%
  of work should be skipped. (V2's skip list was generic.)
- Frame check — three sentences, not paragraphs. Easier to actually do.
- Anti-patterns — three numbered, not buried prose.

What was kept from V2:
- Frame check A and B — the load-bearing additions over V1.
- The eight steps' core structure.
- Failure-mode checks (willfulness, laziness).
- Return-to-one mechanism (folded into the frame check section).

What was cut:
- The locked example from V1/V2 — too narrow, distracting on each invocation.
- The wordy explanations of each step — kept as comments in the
  benchmark report instead.
