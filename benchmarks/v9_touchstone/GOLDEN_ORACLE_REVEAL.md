# The Golden Oracle — what it reveals about an LLM grading its own homework

*(framing note, backed by the v1/v2/Haiku benchmark runs — gitignored draft)*

## The one-sentence idea
A test's **oracle** is whatever decides pass/fail. When an LLM writes tests for code
it also wrote, the oracle it reaches for by default is **the code itself** — so the
test passes by construction and proves nothing. A **Golden Oracle** is an expected
value derived from the **spec**, by hand, *independently of the code*. It is the one
move that exposes the difference, because it is the one move the lazy path cannot fake.

## Two pathologies it shines a light on

**1. Laziness — testing what the code DOES, not what it SHOULD do.**
The path of least resistance is to run the function, see it returns `8500`, and freeze
`assert f(...) == 8500`. The number is "correct" only in the sense that it matches the
implementation. The model has described behavior, not verified intent. This is the
single most common LLM test smell, and it is *invisible on a green board* — every such
test passes, every time, including over a bug.

**2. Self-rigging — the suite is its own grader (circularity).**
Because the oracle is the code, the test and the code can be wrong *in the same way at
the same time*. "Tests pass" then means only "the code agrees with itself." The suite
has been rigged — not maliciously, just by default — to ratify whatever the code does.
A green checkmark on a self-rigged suite is evidence of nothing.

## The Golden Oracle is both the cure and the detector
- **Cure:** derive at least one exact expected value from the *spec*, every step by
  hand, and freeze it. Now a test can disagree with the code — which is the only way a
  test can ever catch a bug. (If your hand-derivation can't be wrong in the same way
  the code is, it's independent. If it caught one of your own arithmetic slips, that
  *is* the signal it's independent.)
- **Detector — the move that unmasks the rig:** **replace the code with a
  spec-correct implementation and re-run the suite.** If the tests *still pass*, the
  oracle was never the spec — the suite cannot tell right code from wrong code. That
  is a self-rig, proven, not asserted.

## What the benchmarks showed (this is the evidence, not a claim)
Across every round, a strong model could *read* a gamed suite and *say* "these look
tautological." The thing it did **not** do without the discipline was **prove it**.
The TOUCHSTONE arms — and only the TOUCHSTONE arms — performed the detector move:
they swapped in the spec-correct implementation (`ROUND_HALF_UP`; `(quantity-1)//10`)
and showed **all tests still pass**. Both blind judges, every round, singled out that
exact step as the decisive evidence and ranked it highest. The lazy suite's tell is
not that it's red — it's that it stays **green for the right answer too**. The Golden
Oracle is what makes that visible.

> **"Tests pass" is not evidence. "Tests fail when the code is broken — and only
> then" is.** A suite that also passes the *correct* code was grading the code, not
> the spec. That is the self-rig, and the Golden Oracle is the lamp you shine on it.

## Why "the tests pass" keeps fooling people (and models)
A passing, ~100%-coverage, reasonable-looking suite *feels* like verification. The
benchmarks are a measured reminder that coverage and green are Goodhart targets: the
suites were green, covered, and honest-looking, and still blind to a live money bug.
The Golden Oracle is deliberately small (one hand-derived number) precisely because
its job isn't breadth — it's to break the circularity at a single, undeniable point.
