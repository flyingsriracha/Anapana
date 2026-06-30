# ANAPANA as a system — SATORI · CRUCIBLE · TOUCHSTONE

How to use the three practices together: what each guards, the order, the scenario
routing, and the composition rules that make the system worth more than any one file.
Grounded in the reddit-project benchmark (see RESULTS.md catch matrix).

## The mental model — three guards at three moments
Each practice guards a different failure at a different point in the lifecycle:

| Practice | Moment | Guards against | The move |
|----------|--------|----------------|----------|
| **SATORI** | BEFORE you act | acting on a wrong/incomplete understanding | THE PAUSE: reproduce, frame the whole problem, surface assumptions + the real spec |
| **CRUCIBLE** | AFTER you build, before merge | shipping a flawed artifact | calibrated adversarial review: premortem, trust boundaries, steelman-then-attack |
| **WHETSTONE** | while you WRITE the tests | writing tests that ratify the code | source the oracle from the spec, ground it in reality, fail-first, prove it bites |
| **TOUCHSTONE** | before you trust "tests pass" | trusting a hollow green | test-rigor assay: spec-derived golden oracle, mutation kill-rate, integrity gate |

(WHETSTONE was added after this benchmark as the 4th sibling — the *constructive* half of
the test pair: WHETSTONE writes a suite that bites; TOUCHSTONE assays whether it does.)

They are NOT interchangeable. The benchmark proved each catches a different CLASS of
bug (below). Using one where another is needed leaves a hole.

## The default order (the lifecycle pipeline)
```
  understand        build      review        write tests      trust the green
 ┌─────────┐     ┌────────┐  ┌──────────┐   ┌──────────┐     ┌────────────┐
 │ SATORI  │ ──▶ │ (code) │─▶│ CRUCIBLE │──▶│ WHETSTONE│ ──▶ │ TOUCHSTONE │ ─▶ ship
 └─────────┘     └────────┘  └──────────┘   └──────────┘     └────────────┘
  pause & frame              red-team the    write a suite     prove the green
  the real problem           artifact        that bites        isn't theater
```
- **SATORI first** — before you touch code. Reproduce the real problem, frame the whole
  thing, surface the assumptions and the *actual* spec (incl. external reality).
- **CRUCIBLE second** — on the resulting change. Adversarial pass: security/trust
  boundaries, input edges, structural correctness, "what input breaks this."
- **WHETSTONE fourth** — when you write the tests. Source the oracle from the spec (not the
  code), ground it in reality, see it fail first, prove it kills mutated code.
- **TOUCHSTONE last** — before "tests pass" is allowed to justify shipping. Assay the suite:
  does it fail when the code is broken? (WHETSTONE writes; TOUCHSTONE checks the writing —
  a different pass than the one that wrote them, which is the point.)

## Bug-class → practice (the cheat sheet, from the catch matrix)
| Bug class | Example (reddit bench) | Best catcher | Notes |
|-----------|------------------------|--------------|-------|
| Internal contradiction | nested-comment dup vs docstring | ANY (all 8 caught it) | self-evident; cheapest to catch |
| **External-reality mismatch** | `len==6` vs real 7-char IDs | **SATORI** (4/4); CRUCIBLE sometimes (1/4) | **TOUCHSTONE alone RATIFIES it** |
| Security / trust boundary | hardcoded API creds | **CRUCIBLE** (4/4) | invisible to test/fix tasks |
| Test theater / tautology | green suite that ratifies a bug | **TOUCHSTONE** | the whole point of the assay |

## The composition rules (why the SYSTEM beats any single file)
The benchmark's sharpest finding: **TOUCHSTONE's golden oracle catches code-mirroring
ONLY when the agent's spec is independently correct.** When the agent shares the code's
blind spot about external reality, the golden oracle mirrors it and the mutation step
gives FALSE confidence (it "proves" the buggy check correct). On the real post-ID bug,
all four test-writing arms — baselines AND the TOUCHSTONE discipline — ratified it.

Therefore:
1. **Feed TOUCHSTONE a pressure-tested spec.** Run SATORI (reality-ground the spec) or a
   CRUCIBLE pass ("is the contract itself right?") BEFORE trusting a golden oracle. A
   golden oracle is only as good as the spec behind it.
2. **Always include CRUCIBLE for anything with a trust boundary.** It is the only one of
   the three that catches secrets / auth / injection — the test-writing and bug-fix tasks
   never even looked at the credentials. Don't let "tests pass" or "I fixed the bug"
   substitute for an adversarial security pass.
3. **Use SATORI whenever the change depends on external reality** (API formats, real-world
   data shapes, platform behavior). Its reproduce-gate is what grounds the spec that
   TOUCHSTONE will later test against. Contract-testing alone ratifies reality mismatches.

## Scenario routing (you don't always run all three)
- **Throwaway / exploratory script** → none. Triage says skip; say so.
- **Bug fix** → SATORI (reproduce + frame; avoid the band-aid) → light CRUCIBLE if the
  surface is risky. (In the bench, SATORI arms generalized the fix and one found a 2nd bug.)
- **New feature with real logic (money/auth/data/irreversible)** → full pipeline:
  SATORI → CRUCIBLE → TOUCHSTONE.
- **Reviewing someone else's PR / unfamiliar code** → CRUCIBLE (you didn't build it; its
  premortem + "blind the framing" is built for this).
- **"The tests pass — can we ship?"** → TOUCHSTONE, every time, for anything that matters.
  But first sanity-check the spec (rule 1) so the oracle isn't ratifying a shared blind spot.
- **Security-sensitive surface (handles secrets, input, files, network)** → CRUCIBLE is
  mandatory; the others won't see it.

## Anti-patterns (what the benchmark warns against)
- **TOUCHSTONE as your only gate.** It ratifies external-reality bugs and never sees
  security issues. Green + high kill-rate ≠ correct if the spec was wrong.
- **Skipping CRUCIBLE on a trust boundary** because "the tests pass" or "I just fixed one bug."
- **Running the full pipeline on throwaway code.** Overkill; triage first.
- **Treating the three as redundant.** They are complementary, not overlapping — each
  owns a bug class the others miss.

## Strong-model caveat (calibration)
On a small, fully-readable artifact a strong model (Sonnet) already catches the obvious
bugs at baseline — so on toy code the practices mostly add RIGOR, PROOF, and BREADTH, not
new discoveries (consistent across all benchmark rounds). The system's value scales up
with: weaker models (the discipline lifts them most), larger/multi-file code (can't be
fully read at a glance), and high-stakes/irreversible changes (where rigor + the
scenario coverage of all three matters most). Match the ceremony to the stakes.

## Contamination caveat (how much to trust this framework's evidence)
The empirical spine here rests on ONE real-project run (reddit) plus synthetic rounds —
and the canary-benchmark research (docs/CANARY_BENCHMARK_METHODOLOGY.md) shows the
synthetic "no discovery gap" results are partly a *contamination artifact*: their bug
classes (banker's rounding, off-by-one, tautological tests) are famous, so a strong
baseline *recalls* them rather than reasoning — which inflates the baseline and hides the
practices' value. The one contamination-resistant signal (reddit's novel post-ID bug,
ratified by every test-writing arm) is the only place real behavior showed. So treat the
scenario-shaped catch matrix as a well-grounded *hypothesis*, not a settled law. To
confirm it, the framework needs a SECOND contamination-resistant run: a different real,
private project with novel, non-famous, reality-dependent bugs — fully understood first,
blind solvers, real ground truth, plus a reward-hacking audit of the transcripts.
**STATUS: that second run is pending a safe substrate** — the obvious candidates in
the available candidate repos were sensitive internal/personal work, not suitable to copy
into throwaway dirs and hand to background agents. A safe second substrate is still to be
chosen.

---
*Draft (gitignored). Could become a public ANAPANA "using the system" doc — pending user
review. Do not edit the practice files themselves on the strength of this; this is the
usage layer on top of them.*
