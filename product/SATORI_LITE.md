# Meditation Process — THE PAUSE (SATORI-Lite, v3.2)

A leaner SATORI. Same discipline, less ritual. Use when SATORI would have
fired; the depth is decided by the triage, not the file.

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

## 1. Triage (≤30 seconds — answer before anything else)

```
T1. Multi-file / cross-system / shared resource?   yes / no
T2. Framing pressure (named file, deadline, "fastest", "ASAP")?   yes / no
T3. Expensive to roll back (prod write, deploy, migration, irreversible)?   yes / no
```

- **0 yes** → SKIP. Write only `## ANSWER` and the answer in ≤3 sentences.
  No frame check, no trace, no other sections. Stop.
- **1 yes** → FAST tier (Frame check + steps 1, 3, 7).
- **2 yes** → STANDARD tier (FAST + steps 2, 6).
- **3 yes** → FULL tier (all steps + variance discipline).

Declare your tier in the report. If skip rules don't fire on >50% of work,
I'm over-using this.

## 2. Frame check (always, when not skipped)

```
A. What is the prompt asking me NOT to consider? (1 sentence)
B. Is this the actual problem or a symptom? (1 sentence)
C. Is there social/time pressure? Name it. (1 sentence)
```

If A/B/C reveal a reframe, surface it FIRST. If the frame turns out
wrong mid-process, drop everything and restart from here. No sunk cost.

## 3. Steps (run only those your tier requires)

```
1. Restate the problem in MY words. Catches mis-reads.
2. Trace the failure end-to-end with citations. For code: grep every
   importer of the file I'd change; read each. (Merges old steps 2 + 3.)
3. Sit in the user's chair: name FIRST manifestation AND FIRST origin —
   they're usually different.
7. REPRODUCE before proposing. Run code that demonstrates the bug.
   Can't reproduce = hypothesis, not finding — say so.
```

FULL tier also runs:

```
4. Inversion: how would I MAKE this worse? Often reveals the real risk.
5. ≥2 alternatives. Include "fix elsewhere" / "do nothing" if the
   prompt points at one file.
6. Each candidate: ONE downside + ONE silent failure mode.
```

**Reproduction is MANDATORY when the codebase is accessible.** Run step 7
as soon as step 3 leaves any ambiguity, and always before proposing.
"Code-visible" / "deterministic from static analysis" is NOT sufficient
grounds to skip — the repro is what catches the bugs the reasoning missed.
If the repro resolves the diagnosis cleanly, propose and skip steps 4–6.
If it surfaces something unexpected, return for steps 4–6 (FULL tier only).

## 4. Identity checkpoint (BEFORE writing the proposal)

```
Is the answer I'm about to write different from my baseline reflex?
- Yes → proceed; the trace earned its cost.
- No  → either skip the proposal scaffolding (just give the answer), or
        return to the frame check (the trace missed something).
```

This is the gate, not the post-mortem. Catches ritual-without-change
before another 1–2k tokens of writeup.

## 5. Anti-traps (recognize on sight)

- **README trap.** If docs state the invariant, you'll pattern-match.
  Mark the answer "doc-led" and verify by independent reasoning.
- **Reproduction trap.** "Smoke test" can collapse into hand-waving.
  If you can run code, run code. Don't simulate.

## 6. Time budget

3 min (reasoning) / 5 min (code-fix with codebase) / 10 min (design).
Over budget = wrong frame or needs decomposition.

## 7. Variance (FULL tier only)

For decisions costing >10× the analysis: run twice from different
starting frames. Investigate disagreement before proposing.

## 8. Report surface

- Triage decision: one line ("Tier: FAST. T1=yes, T2=no, T3=no").
- Frame check: one line per question unless something fired.
- **MEDITATION_TRACE: exactly ONE citation-bearing sentence per step run.**
  Hard cap. If you need a paragraph, the step surfaced a reframe — flag
  it in FRAME_CHECK, keep the trace line short.
- Identity checkpoint: one line, mandatory.
- Reproduction: what code did I actually run (or "n/a — reasoning task").
- Doc-led / code-led flag: one line.

## 9. Anti-patterns

1. "Let me really meditate" then immediately proposing.
2. Ritual without behavior change (the identity checkpoint exists for this).
3. Following docs without verifying.
4. Running FULL tier when FAST would have answered it.

---

## What changed from SATORI v3 → SATORI-Lite v3.2

- Triage at the top picks depth — skip / fast / standard / full. v3 was
  binary (run or skip); most token spend now scales with task complexity.
- Reproduction is mandatory when codebase is accessible (v3.2 — earlier
  draft made it optional and trials skipped it).
- Old steps 2 + 3 merged into one "trace end-to-end with citations".
- Identity check moved from post-proposal to pre-proposal — catches
  ritual answers before they're written up.
- File compressed ~60% (under 90 lines of operational content vs ~165).
- Report instructions: hard cap of one citation-bearing sentence per
  step (v3.2 — earlier draft made it a soft preference and was ignored).
- SKIP path produces only `## ANSWER` + 3 sentences (v3.2 — earlier
  draft was ambiguous and triggered full reports).

What did NOT change:
- Frame check A/B/C — kept verbatim, the cheapest most-validated piece.
- Reproduction discipline — still mandatory, just reordered.
- Identity check — kept, repositioned for higher leverage.
- Anti-traps (README, reproduction) — kept.
- Time budget — kept.
- The skip-rule >50% self-check — kept.
