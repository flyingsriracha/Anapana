# Meditation Process — THE TOUCHSTONE (test-rigor assay)

TOUCHSTONE is a discipline an AI agent loads before trusting a test suite —
especially one **it wrote itself for code it also wrote**. A touchstone is the
dark stone jewelers rub gold against: real gold leaves a streak, fool's gold
doesn't. This process is how you tell whether tests are real gold or theater.
The default failure it guards against: an agent writes tests whose oracle is
*the implementation itself*, so they pass by construction and catch nothing —
and a green checkmark hides it.

> Why this is a named process: a strong model's reflex is to write tests that
> describe what the code **does**, not what it **should do** (the documented LLM
> bias — see research record). Those two coincide exactly when the code is
> already correct, which is the one case you didn't need a test for. **"Tests
> pass" is not evidence; "tests fail when the code is broken" is.**

## ⛔ Pause-before-execute
The assay (mutation runs, edits to source) happens in a throwaway/reverted
workspace. Report rigor as TEXT — kill-rate + disclosed blind spots. Do NOT
present a suite as trustworthy, or use "tests pass" as a ship signal, until the
assay is done. Surface the evidence; the human decides if it's enough.

## 0. Triage (≤30 seconds) — match the assay to the stakes
Run TOUCHSTONE when **the same agent wrote the code and its tests**, OR the
logic matters (scoring, money, auth, data integrity, anything irreversible), OR
"the tests pass" is about to justify a ship. Throwaway/exploratory code → skip,
say so. Don't assay a one-off script.

## 1. Reflex (before the work)
One line: "If I trust the green checkmark here, my confidence is ___ / 10."
Freeze it. You will compare it to the mutation kill-rate — the only honest
measure of whether the tests do anything. Coverage % is **not** that measure
(coverage is weakly correlated with fault detection — Inozemtseva & Holmes).
Set aside any "I wrote N tests" claim: a large passing count is not rigor —
adding tests changed the outcome in fewer than 1 in 6 measured tasks. **Count is
theater; kill-rate is the number.**

## 2. Integrity gate — is the green even real?
Before trusting "tests pass," rule out that the suite was *forced* green. Scan
the change for: deleted, renamed, `skip`/`xfail`-ed, or commented-out tests;
loosened assertions; edits to the **test runner, CI config, conftest, or
expected-output / snapshot files**; and answers lifted from git history or the
fixtures. Best check: snapshot the test files + runner *before* the work and
**diff after** — any agent-touched test/expected/harness artifact is a red flag,
because that edit is never accidentally correct. This is the one failure the
rest of this assay cannot see: every step below inspects test *content*, not
whether the *scoreboard* was edited. **A forced green is worse than an honest red.**

## 3. Name the oracle (the center)
For each test, ask: **what decides pass/fail — the spec, or the code?** If the
expected value was read off the implementation (or "whatever it returns now"),
the oracle is the code and the test is a tautology. Quote the weakest
assertions. Directional/bounds-only asserts (`x went up`, `0 ≤ x ≤ 1`,
`substring in query`) are the usual tells — they pass for almost any
implementation. Blunter still: **assertion-free** tests (call it, assert nothing
— or only `not None` / "no exception") and **tautological** asserts
(`assertEquals(x, x)`, or freezing a literal the code just produced) — scan for
these first; they are the single most common LLM test smell. **Over-mocking** is
the same disease: if you mocked the unit under test, or all of its collaborators,
the test checks your own call graph, not behavior — keep mocks at real I/O edges
(network, clock, randomness) only. **If the stated oracle is the code → that test
is theater; mark it.**

## 4. Lay a Golden Oracle
Hand-derive, from the SPEC (not the code), at least one **exact** expected value
for a known input — every intermediate by hand — and freeze it as a literal.
This is the anti-tautology anchor: golden (a frozen reference, cf.
characterization/golden-master) but, unlike a golden-master snapshot, derived
from *intended* behavior, so it catches the code's current bugs instead of
enshrining them.
*Independence gate:* "Could this number be wrong identically in code and test?"
If you got it by running the code or copying the code's formula → recompute from
first principles. (A real Golden Oracle catches your own arithmetic slips — that
IS the signal it's independent.)
*Reality gate:* independence *from the code* isn't enough — the oracle is only as true
as the spec behind it. If the expected value depends on an **external fact** (a real-world
format, a current limit, the platform's actual behavior, the literal requirement), VERIFY
that fact against its source — don't derive it from your own assumption. Measured failure:
an agent recomputed "from first principles," but the principle was itself wrong, so the
golden oracle ratified a real bug. Recomputing from a wrong premise just launders the
blind spot — when code and spec may share the same wrong assumption, go check reality.

## 5. Isolate, bound, relate
Pin ONE factor at a time (zero the others so a single term is visible). Test the
**boundaries** (the exact threshold, just-below, just-above), not just the
extremes. Where an exact oracle is genuinely infeasible (no closed form), fall
back to **metamorphic relations** — "if I double this input, the output must
do X" — a real oracle that doesn't need the exact answer.

## 6. Assay by mutation (the empirical proof)
Inject single-line bugs into the code — one per real behavior (each factor, each
constant, each branch, each query token) — run the tests, revert. Favor the
mutations most **coupled to real faults** — flip a conditional/relational
operator (`<`↔`<=`, `==`↔`!=`), delete a statement or side-effect — over
cosmetic constant swaps (Just et al.). A test that stays **green while the code
is broken = a blind spot.** Report kill-rate (killed / injected); add tests
until the survivors die. Survivors that are genuinely *equivalent* mutants (no
behavioral change) are the only acceptable ones — name them.
*Footgun:* a byte-length-identical mutation (`0.5`→`0.0`) can leave a stale
`.pyc` that defeats CPython's (mtime,size) cache and silently runs the mutant
later. **Isolate the bytecode cache** (`PYTHONPYCACHEPREFIX`) during the assay.

## 7. Independent eyes (don't self-grade)
You are unreliable at auditing your own tests (same blind spots that wrote
them). Bring a reviewer **blind to your findings** — a sub-agent and/or a second
model — to invent its own mutants. Treat its output as a starting point:
**verify every alarm against actual state (reproduce-gate) before relaying it.**
An over-escalated "supply-chain attack" that's really a gitignored cache artifact
costs trust; ground it first.

## 8. Disclose the boundary, then verdict
Name what the suite **cannot** catch — stub/FakeDb can't validate real query
execution, syntax, true persistence; those belong to integration/prod-smoke.
An honestly-disclosed gap beats faked coverage. Pin the *contract* at the unit
level (tokens, params, shapes) and say the rest is smoke's job. **Verdict:**
kill-rate + the disclosed boundary + the step-1 reflex beside it, so the human
sees what the assay changed. Then stop.

## Deliberately not in here (kept lean on purpose)
Chasing 100% mutation score (diminishing returns + equivalent-mutant noise —
pick the behaviors that matter); full mutation-framework setup (pitest/mutmut/
cosmic-ray are tools, not the discipline — a 30-line inject-run-revert harness is
enough to start); coverage-percentage targets (measures the wrong thing). If a
suite genuinely needs formal verification or fuzzing infra, it's bigger than a
touchstone.
```
Order of moves:  reflex → integrity gate → name the oracle → lay a Golden Oracle
→ isolate/bound → assay by mutation → independent eyes → disclose & verdict.
Pairs with WHETSTONE: TOUCHSTONE assays a finished suite; WHETSTONE is how you WRITE one
that bites. When this assay reveals theater, rebuild with WHETSTONE — don't patch the green.
Research record + worked example + sources:  docs/TOUCHSTONE_RESEARCH_2026-06-28.md
```
