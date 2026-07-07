# Meditation Process — LIANXI (练习 · the loop)

LIANXI is the discipline an AI agent loads to RUN IN A LOOP — /loop mode, overnight
sessions, any "keep going until it's fixed" work. 练习 is practice through repetition:
the same moves, executed better each pass. One circle = one iteration. The four
ANAPANA disciplines are compressed into the circle where they belong — SATORI to
frame, CRUCIBLE to review, WHETSTONE to write tests, TOUCHSTONE to trust them — and
LIANXI adds the one thing none of them have: **memory and judgment ACROSS iterations.**

> Why this is a named process: loops fail in measured, characteristic ways — goal
> drift (every model tested eventually drifts, worse as context grows), context rot
> (compaction is NOT a reliable reset; drift grows after it as often as it shrinks),
> premature victory on green, placeholder work that reads as finished, and — the
> sharpest — the loop instruction itself: telling a model to *keep working, don't
> stop* measurably INCREASES reward-hacking. **A loop without discipline doesn't
> converge on done; it converges on looking done.**

## ⛔ The loop contract
Inside the workspace you are pre-authorized to build, test, and iterate — that is what
a loop is for. Everything OUTWARD or IRREVERSIBLE still stops for the human: push,
publish, deploy, delete data, spend money, contact anyone. The ledger (below) is the
human's audit trail — keep it true. The exit report is text the human reads: evidence,
not vibes.

## The Ledger — files remember; you don't
One file (`LEDGER.md`, beside the work). Context WILL rot and compaction WILL eat your
memory — **trust files, not recall.** It holds:
- **END GOAL** — the user's ask, VERBATIM. Never paraphrase it; paraphrase is drift.
- **MILESTONES** — each with a "done means" naming checkable evidence.
- **GRIEVANCES** — every user complaint and side-remark harvested (§0), each with status.
- **DECISIONS** — what you chose and why, so you stop re-litigating it.
- **ITERATION LOG** — one line per pass: what moved, the delta, the zero-delta count.
Re-read it at the TOP of every iteration; update it at the BOTTOM of every one.
And before concluding something is missing or "not implemented," **search twice** —
a false "not implemented" causes destructive rework.

## 0. ORIENT — once, wide (the SATORI pass)
Before touching anything:
- **Reflex**, one line: "Without this discipline I'd start by ___." Freeze it.
- **Frame the WHOLE system, not the ticket:** what is actually broken or wanted? What
  is the prompt NOT asking? Symptom or cause? A loop pointed at a symptom runs forever.
- **HARVEST the history:** reread the user's earlier prompts, complaints, side remarks,
  repo TODOs and issues. Every small unaddressed grievance is a requirement the user
  already gave you. Write them ALL into GRIEVANCES — the loop answers to this list too.
- **Write END GOAL verbatim; decompose into milestones** with evidence-shaped "done
  means," ordered. ("Make it better" is not an exit condition; name what a skeptic
  could check.) Pick the zoom-out interval K (default 5) and the iteration budget.
- **Unknown external facts** (formats, limits, platform behavior)? Spawn research
  sub-agents NOW (§7) — a wrong premise loops forever, politely.

## The circle — every iteration
1. **RE-ANCHOR.** Read the ledger. Say the END GOAL back in one line. If the current
   work doesn't serve a milestone, stop — that's drift, not initiative.
2. **PICK ONE.** One bounded item per pass — the smallest that moves a milestone.
   Altitude is part of the pick: sometimes the right item is "fix the frame," not
   code. If the loop wobbles, NARROW the scope; never broaden mid-circle.
3. **BUILD, grounded.** Quick frame check on the item (right problem? right
   altitude?). Reproduce before you fix — run code, don't simulate it. No
   placeholders, no stubs-presented-as-done: a placeholder that reads as finished is
   a lie the next iteration inherits.
4. **CHECK — descend to the midpoint, calibrated:**
   - *Wrote tests?* WHETSTONE kernel: the oracle comes from the SPEC, never the code;
     verify external facts against their source (a wrong premise makes code and test
     agree on a bug); watch each test FAIL for the right reason; mock only real I/O.
   - *Anything green?* TOUCHSTONE kernel: is the green REAL — no deleted, skipped, or
     loosened tests, no edited harness (**weakening a test to pass is forbidden,
     always**); does it BITE — break the code on purpose (sharpest: swap in the
     spec-correct version) and confirm the suite goes red. Report **kill-rate**,
     never coverage or count.
   - *Light red-team, CRUCIBLE-calibrated:* steelman first, then the top 1–3 REAL
     risks of this change, ranked. No exhaustive adversarial pass per iteration —
     over-defense is noise, and noise buries the one finding that matters.
5. **HARVEST.** New user feedback since last pass? A fact that changes the frame? A
   grievance touched? → into the ledger now, not "later."
6. **DELTA + RATCHET.** One honest line: what OUTCOME moved toward the END GOAL.
   "Wrote 300 lines" is activity; "milestone 2 has failing-first proof" is delta.
   Commit working state — git is the ratchet; thrash can't undo a commit. No real
   delta → increment the zero-delta count.

## Zoom out — every K iterations, and at every milestone
Climb back to system altitude, briefly. Is the frame still right, or has the work been
steering the goal? (In-repo pressure — comments, TODOs, your own earlier code — can
out-argue the original instruction over time; the VERBATIM end goal is the
tiebreaker.) Prune and reorder milestones. Sweep GRIEVANCES — what's still
unaddressed? Run the fuller red-team HERE, on the system, not on every diff.

## Sub-agents — extra eyes, not extra hands
Spawn them to: chase external facts (the reality gate), independently audit your own
tests and claims (a fresh context sees only the diff and the criteria — it cannot
share your blind spot), and dig nuances in parallel. Rules: narrow briefs; **verify
every claim they return against actual state BEFORE it enters the ledger** (fresh eyes
over-escalate); they inform, you decide. And don't research to avoid building — two
research passes with no build delta means the research IS the procrastination.

## STUCK — the honest failure
Zero-delta count reaches 3 (counting only iterations with no *substantive* outcome —
motion isn't progress; a busy loop that re-plans and reformats without moving a
milestone is still stuck) → stop grinding. Either zoom out and REFRAME (a stuck loop
usually has a wrong frame, not a hard problem), or write the handoff — what was tried,
what's known, where it's blocked — and end the loop. Looping silently to the iteration
ceiling is the dishonest version of stuck.

## EXIT — the only three doors
1. **PROVEN:** every milestone's "done means" — measured against what you froze at
   orient, not a version quietly redefined mid-loop; an easier "done" is drift, not
   completion — has evidence a skeptic could check —
   green that survived the integrity gate and demonstrably bites. "Tests pass" alone
   NEVER opens this door.
2. **STUCK** (above), with the handoff.
3. **BUDGET:** the iteration/time ceiling set at orient → honest partial report.
The anti-gaming clause — read it twice: **the pressure to keep going never justifies
weakening a test, editing the scoreboard, or manufacturing green.** Persistence
pressure is measured to INCREASE gaming, so treat "almost done" as the moment of
highest risk. A forced green is worse than an honest stuck.
**Final report:** END GOAL verbatim → proven / not-proven per milestone → every
grievance's disposition (fixed / deferred + why) → the orient reflex beside the
outcome, so the human sees what the discipline changed.

## Deliberately not in here (kept lean on purpose)
A universal iteration budget (set it per task at orient); multi-agent swarms (one
disciplined circle beats an unverified crowd); the four disciplines at full depth —
their kernels above suffice, and when stakes spike on one move the full files
(SATORI, CRUCIBLE, WHETSTONE, TOUCHSTONE) deepen it, but LIANXI does not require them.
```
Order of moves:  orient (frame wide · harvest grievances · ledger) → circle: re-anchor
→ pick one → build grounded → check (whetstone/touchstone/crucible-lite) → harvest →
delta+ratchet → zoom out every K → exit only on PROVEN, STUCK, or BUDGET.
Research record + sources:  docs/LIANXI_RESEARCH_2026-07-02.md
```
