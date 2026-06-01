# SATORI token-reduction proposal (DRAFT — not yet adopted)

Goal: cut SATORI's per-invocation token cost without losing the discipline
that made it land on the Pareto frontier (same quality as INSIGHT,
30–60% faster, 13% fewer tokens).

This is a draft for the user to review before changing the practice file.

---

## Where the tokens actually go

A SATORI invocation spends tokens in five buckets. Listing them so we cut
the right ones:

1. **The meditation file itself** — included in every prompt. ~1.5k tokens.
   Fixed cost paid even on tasks the practice ends up skipping.
2. **The frame check (A/B/C)** — small generation cost. ~150–300 tokens.
3. **The 8-step trace** — the largest variable cost. ~3–8k tokens of
   reasoning per task, scaling with how thoroughly each step is performed.
4. **The reproduction step** — code generation + execution. ~1–3k tokens
   when it fires; the highest *value* per token in the benchmark.
5. **The structured report output** — the MEDITATION_TRACE / FAILURE_MODE
   / etc. sections. ~1–2k tokens of post-hoc writing.

The 8-step trace dominates. Cutting it without losing quality is the lever.

---

## Hypothesis: the current discipline is one-size-fits-all

Right now the gate is binary: invoke or skip. If invoke, run all 8 steps
at the same depth regardless of how revealing the early steps were.
Two consequences:

- **Trivial-but-non-skippable tasks** get the full 8-step pass when 3
  would have caught the answer.
- **Steps 4-5 (inversion + alternatives) are make-work** when step 3
  ("sit in user's chair") already surfaced the answer. The benchmark
  trials showed many traces where step 5's "alternative" was strawman
  filler so the checklist could be completed.

If the practice could tier its own depth and exit early when an early
step decides the question, we'd keep the quality and lose the bulk.

---

## Proposed process (the changes I'd make to SATORI.md)

### 1. Add a 30-second triage at the top

Replace the prose "When to invoke" list with three explicit yes/no
questions the agent answers before deciding what depth to run at:

```
□ Triage (3 questions, ≤30 seconds):
   T1. Does this touch multiple files, processes, or systems? (yes/no)
   T2. Is the prompt applying framing pressure (named file, deadline,
       "fastest", "ASAP")? (yes/no)
   T3. Is the action expensive to roll back (DB migration, prod write,
       deploy, irreversible decision)? (yes/no)

   0 yes → SKIP. Just do the work.
   1 yes → FAST tier (frame check + steps 1, 3, 7).
   2 yes → STANDARD tier (frame check + steps 1, 2, 3, 6, 7).
   3 yes → FULL tier (all 8 steps).
```

**Why this saves tokens:**
- 0-yes path skips ~5–8k tokens of meditation entirely.
- FAST tier saves ~3–5k tokens vs FULL by skipping inversion,
  alternatives, downside enumeration.
- STANDARD still gets the consumer-grep (step 2) and downsides
  (step 6) — the steps that did the work in B2 and B3.

### 2. Reproduce-first when the codebase is accessible

Reorder: if step 7 (REPRODUCE) is feasible, run it BEFORE steps 4-5
(inversion + alternatives). Rationale: the reproduction often answers
the question that inversion/alternatives were trying to answer by
reasoning. When it does, skip 4-5 entirely.

Encoded as a one-line rule:

```
If the language supports running code AND step 3 left ambiguity:
   skip to step 7. If repro resolves diagnosis, propose (step 8). Done.
   If repro is inconclusive, return and run steps 4-5.
```

### 3. Merge steps 2 + 3

Steps 2 (macro frame / grep importers) and 3 (sit in user's chair /
trace row-by-row) overlap heavily — both produce a system view with
file:line citations. Merging into one step ("Trace the failure
end-to-end with citations, including every importer of the file
you'd change") drops a step's worth of generation without losing
either's contribution.

### 4. Compress the meditation file itself

Current file is 209 lines including design notes. The instructional
core is ~80 lines. Cutting prose (the "why" of each step is mostly
implicit) gets the file to ~50 lines. Cost saving is small per
invocation (~500 tokens) but it's paid every single time, including
on skipped tasks.

### 5. Cap MEDITATION_TRACE output

Add to the report instructions: "Each step: one citation-bearing
sentence unless the step surfaced a reframe, in which case write a
paragraph." Forces the trace to be a record of what happened, not
a re-derivation of the reasoning.

### 6. Make the identity check the gate, not the close

Move the IDENTITY check ("is my answer different from baseline-reflex?")
from step 8 to a checkpoint between trace and proposal:

```
Mid-checkpoint: would I have proposed this answer without the trace?
   - Yes, identical → the trace was ritual. Either skip the rest, or
     return to frame check (the trace missed something).
   - No, different → the trace earned its cost. Proceed to step 8.
```

This catches "ritual without behavior change" earlier — before another
1–2k tokens go into writing up the proposal.

---

## What I'm NOT proposing

- **Don't drop the frame check.** It's the cheapest part and the most
  benchmark-validated. Three sentences max — keep it.
- **Don't drop the reproduction step.** It's the highest-value step in
  the practice; the change is *ordering*, not removal.
- **Don't add steps.** [[feedback-no-more-steps]]. The proposal
  removes / reorders, never adds.
- **Don't strip the cost honesty.** The "If skip rules don't fire on
  >50% of work" line stays — over-use is the failure mode.

---

## Expected savings (to be measured)

Without measurement these are estimates. The fair rerun I'm running now
gives us SATORI-baseline numbers; a SATORI-Lite rerun on the same
problems would tell us the real number.

| Lever | Estimated saving | Risk |
|-------|-----------------:|------|
| Triage skip on no-yes tasks | 100% for ~30% of tasks | Tasks slipping through the skip gate |
| FAST tier on 1-yes tasks | 30–50% per task | Missing hidden issues that step 4-5 would have caught |
| Reproduce-first reorder | 20–30% on tasks where repro resolves diagnosis | None expected — pure ordering |
| Merge steps 2+3 | 10–15% per task | Loss of distinction between consumer-graph and trace |
| File compression | ~5% per invocation | None expected |
| Trace compression | 20–30% on report output | Loss of detail that helped post-hoc analysis |
| Identity-check as gate | Cuts wasted proposal writing | None expected |

Combined optimistic case: SATORI-Lite at ~50–60% of current SATORI cost
on the typical task, with identical quality on tasks where the early
steps already converged.

---

## How to validate before adopting

Build SATORI-Lite as a separate file. Run it on B1/B2/B3 (2 trials each).
Compare to SATORI numbers in `results_data.json`:

- If quality (hidden-issues-found, surface-bug correctness) holds → adopt.
- If FAST tier produces baseline-quality results on STANDARD-tier
  problems → triage rule needs to be stricter.
- If reproduce-first reorder breaks anything → revert that one lever.

Same scoring rubric, same problems, same comparison. Empirical, not
asserted.

---

## Recommendation

Highest-value single change: **the triage + tiered depth.** Captures
most of the savings, lowest risk of quality loss because the deeper
tiers are intact for the tasks that need them.

If you want me to draft `product/SATORI_LITE.md` reflecting these
changes, say the word and I'll write it. Then we benchmark it the same
way we benchmarked V3.
