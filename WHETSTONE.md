# Meditation Process — THE WHETSTONE (writing tests that bite)

WHETSTONE is a discipline an AI agent loads **before and while writing tests** —
especially tests for code it also wrote. Its sibling TOUCHSTONE *assays* a finished
suite (is this gold or theater?); WHETSTONE is how you grind each test until it leaves
a real streak. The default failure it prevents: writing tests whose oracle is the
*implementation itself*, so they pass by construction, catch nothing, and a green
checkmark hides it.

> Why this is a named process: a strong model's reflex is to write tests that describe
> what the code **does**, not what it **should do** — and on buggy code that reflex
> *encodes the bug as the expected value*. More than 99% of LLM-generated tests pass on
> the original code; oracle accuracy drops below 50% once the code is buggy (the model
> reads the bug as the spec — see research record). **"Tests pass" is not the goal. "A test that fails when —
> and only when — the code is wrong" is.** A test you have never seen fail is
> documentation with an assertion that might itself be wrong.

## ⛔ Pause-before-execute
Writing/running tests in a throwaway workspace is fine. Reporting is not: present the
tests AND the evidence they bite (the failing-first proof + the mutation kill-rate) as
TEXT. Do NOT claim a suite is trustworthy, or use "tests pass" as a ship signal, until
that evidence exists. Surface it; the human decides if it's enough.

## 0. Triage (≤30 seconds) — match the rigor to the stakes
Run WHETSTONE in full when **you wrote (or will write) both the code and its tests**,
OR the logic matters (scoring, money, auth, data integrity, anything irreversible), OR
"the tests pass" is about to justify a ship. Throwaway/exploratory code → write a
sanity test, say it's only that, move on. Don't over-grind a one-off script.

## 1. Source the oracle from the SPEC, not the code
Before writing a single assertion, decide where the expected value comes from. Two
sources, only one has fault-catching power: the **spec** (requirement, docstring,
standard, domain definition) catches bugs; the **implementation** ("whatever it returns
now") cannot — it ratifies them. If you got the expected value by running the code,
you've written a *characterization* test (legitimate for locking down legacy behavior)
— **label it as such, and do not count it as a correctness test.** Copying computed
values into the expected field defeats the whole point (Beck, *Canon TDD*).

## 2. Ground the SPEC in reality (the meta-oracle gate)
The oracle is only as true as the spec behind it. The most dangerous failure is a
*wrong spec*: the agent's own notion of the requirement is mistaken, so it writes a
plausible implementation AND plausible tests that **mutually ratify a real bug** — a
silent wrong answer (documented: arXiv 2601.05542; reproduced in our own benchmark,
where every test-writing arm "confirmed" a buggy `len==6` ID check because the agents
all wrongly believed IDs were 6 chars). So: if the expected value depends on an
**external fact** — a real-world format, a current limit, the platform's actual
behavior, the literal requirement — **verify that fact against its source** (read the
doc/RFC verbatim, look at real data, ask a second model given only the spec). Do not
derive it from your own assumption. Recomputing "from first principles" launders a wrong
premise. When code and spec might share the same blind spot, your oracle will too.

## 3. Hand-derive at least one exact golden value
Trace the algorithm **by hand** on a known input — every intermediate step shown — and
freeze the result as a literal. This is the anti-tautology anchor (shared with
TOUCHSTONE's Golden Oracle): a frozen reference derived from *intended* behavior, so it
catches the code's current bugs instead of enshrining them. *Independence check:* "Could
this number be wrong identically in code and test?" If you can't trace it by hand, the
spec is under-specified — resolve that before writing the assertion.

## 4. Watch it fail — for the right reason
Never trust a green you haven't seen red. Two cases:
**New code:** classic red-green — write the test from the spec, watch it fail, then
implement. **Existing code** (the usual agent case): a spec-correct test *should* pass
— so **manufacture the red**: temporarily break the behavior under test (a one-line
mutation) or invert the assertion, confirm the test goes red for the right reason,
revert. A test that cannot be made to fail is theater — this is the mechanical break
in the circularity loop. **If the test fails against the current code as-is: stop —
that may be a real bug, not a test bug.** Re-check the golden value and the reality
gate; if they hold, you've found a defect — report it, don't "fix" the test to match
the code.

## 5. One behavior per test; name the behavior
One Arrange-Act-Assert (Given-When-Then) per test: one "when," one "then." Name the test
for the behavior and outcome, not the method — `<system>_<condition>_<expected>`, so with
the suite name it reads as a specification sentence. No `if`/`for`/branching inside a
test body — that's two tests wearing a trenchcoat (Meszaros). A multi-behavior test
passes when one behavior is broken and gives no diagnostic when it fails.

## 6. Test the contract; cover the edges
Assert observable outputs and state changes **through the public surface**, not internal
calls or private state — so a refactor doesn't break the test but a real bug does
(change-detector tests do the opposite). Then leave the happy path: for each input,
enumerate **equivalence classes and boundaries** — below-min, min, min±1, a nominal
value, max, above-max; for collections empty / one / exactly-at-capacity. Defects
cluster at boundaries (Myers); the nominal case is the one least likely to bite.

## 7. Properties & metamorphic relations where an exact oracle is hard
When you can't state the exact answer but can state an invariant, write a **property**:
round-trip (encode∘decode = identity), idempotency, monotonicity, "result always within
legal range." When you can't even state an invariant on one output, use a **metamorphic
relation** — a required relationship between outputs of related inputs ("double the
input → double the result"). Where the function is pure and an invariant
is crisp, one property test buys a thousand examples (Hypothesis `@given`) — don't
force properties onto CRUD/glue; situational, not mandatory. Reserve example tests
for specific known-important cases.

## 8. Mock only the real I/O edges
Doubles are for the trust boundary, nothing else: network, clock, randomness,
filesystem. **Never mock the unit under test** (tautology), value objects (use the real
ones), or every collaborator (then you test your own call graph, not behavior). Agents
over-mock — measured 36% vs 26% for humans, almost entirely `mock` where a `fake` or the
real object would verify more. If a test mocks more than the I/O edge, it earns scrutiny.

## 9. Prove it bites — then hand it to TOUCHSTONE
Tests are not done because they're green; they're done when they **kill broken code**.
Mutate the implementation — flip a conditional (`<`↔`<=`, `==`↔`!=`), change a constant,
delete a statement, and (the sharpest) **swap in the spec-correct version** — and confirm
a test dies for each. Report **kill-rate**, never coverage % or test count (both are
Goodhart targets — assertion-free tests inflate them while catching nothing; mutation
score predicts real fault detection, coverage doesn't — Just et al.; Inozemtseva &
Holmes). A surviving mutant is a spec gap: add a test until it dies — unless it's a genuinely
*equivalent* mutant (no behavioral change): name those and move on; don't chase 100%.
Then run TOUCHSTONE
on the result as an independent assay — a different pass than the one that wrote them.

## Deliberately not in here (kept lean on purpose)
Chasing 100% coverage or 100% mutation score (diminishing returns + equivalent mutants —
pick the behaviors that matter); full mutation-framework setup (pitest/mutmut/stryker are
tools, not the discipline — a 30-line inject-run-revert harness is enough to start);
snapshot-everything (those are characterization tests — see step 1). If the stakes
justify it, a genuinely independent test-author (a separate agent given only the
spec + signature, never the body) and an adversarial mutant-generator loop catch more —
but that's heavier infrastructure than a single discipline.
```
Order of moves:  triage → source the oracle from the spec → ground the spec in reality
→ hand-derive a golden value → watch it fail → one behavior + name it → contract + edges
→ properties/metamorphic → mock only I/O edges → prove it bites → hand to TOUCHSTONE.
Pairs with TOUCHSTONE: WHETSTONE writes/grinds; TOUCHSTONE assays. Reach for WHETSTONE
when TOUCHSTONE reveals theater — rebuild the suite, don't patch the green.
Research record + sources:  docs/WHETSTONE_RESEARCH_2026-06-30.md
```
