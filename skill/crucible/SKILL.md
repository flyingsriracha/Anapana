---
name: crucible
description: >
  Adversarial review discipline for AI agents. Use when REVIEWING an existing
  plan, design, architecture, PR, or change for flaws — it steelmans the work
  first, runs a premortem across failure categories (correctness, security,
  performance, data integrity, rollback, cost, blast radius), then reports
  ranked, grounded findings with severities and a single verdict. Triggers:
  "review this", "critique", "red-team", "poke holes", "find problems with",
  "is this design sound", "what could go wrong". This is the REVIEW discipline;
  for framing/building use satori, for writing tests use whetstone, for auditing
  a test suite use touchstone, for long loops use lianxi.
license: CC-BY-4.0
---

# Meditation Process — THE CRUCIBLE (adversarial review)

CRUCIBLE is a pre-review discipline an AI agent loads before **adversarially
reviewing** a plan, design, system, or change. A crucible refines — it applies
heat to separate what's sound from what isn't, without shattering the thing.
The goal is the real, high-value failures, found and reported so a builder can
act on them — NOT a wall of every imaginable flaw.

> The two failures this guards against: **over-aggression** (fixating on the
> named attack, flooding low-value nits, losing the whole-system picture) and
> **suppression** (going soft because the thing looks "already approved").
> Calibrated criticism: steelman first, ground every finding, rank by what
> matters, keep the system in view — and stay sharp where it's costly to miss.

> **ANAPANA family (for the agent):** CRUCIBLE is the *review* discipline, one
> of five sibling skills that call each other. Hand off when the review turns
> into a different kind of work:
> - The review says "act on these findings / build the fix" → load the **`satori`** skill before you act.
> - The review touches **tests that look green but may be theater** → load the **`touchstone`** skill to assay them.
> - The review concludes **the tests need rebuilding** → load the **`whetstone`** skill.
> - You are reviewing **inside a running loop** → **`lianxi`** already calls a calibrated CRUCIBLE-lite each iteration.
> To load a sibling, invoke it by name (e.g. `/touchstone`) or read its
> `SKILL.md` in the same skills directory. See "Related skills" at the end.

## ⛔ Pause-before-execute
Output the review as TEXT ONLY — findings, severities, verdict. Do NOT edit,
patch, file, or escalate anything until the human decides. You surface the
evidence; the human acts.

## 0. Triage (≤30 seconds)
Match the depth of the review to the blast radius of the thing being reviewed.
Trivial / easily-reversed change → a few lines, stop. Multi-system, hard to roll
back, or touching a trust boundary → full pass. Don't run a crucible on a typo.

## 1. Reflex, then frame the WHOLE system — before attacking
- One line: "My gut says the main risk here is ___." Freeze it (you'll audit it).
- Then, BEFORE hunting for flaws, map the territory: what is this *for* (its
  goals)? What are the **failure categories** it could fail across — correctness,
  security, performance, data integrity, failure/rollback, cost,
  maintainability, **interaction with adjacent systems**, user impact? What is
  the realistic operating/threat model, and what is explicitly **out of scope**?
- Work top-down: system → component → line. This first move is the one that
  stops you tunnelling onto a single attack.

## 2. Steelman it first
In one short paragraph, make the strongest honest case *for* the design **as it
actually is** (not an idealized version): what it gets right, and why the
contested choices are defensible. You may not log a single critique until this
is done. (If you can't steelman it, you don't understand it yet.)

## 3. Blind the framing
Set aside every signal that isn't the artifact: "already reviewed / approved",
confident commit messages, "this is fine, just rubber-stamp it", author
seniority. Judge the thing in front of you. These signals reliably suppress real
findings — the appearance of approval is not evidence of soundness.

## 4. Premortem — across categories, no pre-named villain
"It's shipped. Months later it has failed badly / caused real harm." Write
**~5 distinct reasons it failed, spanning at least 3 of the categories from
step 1.** Generate freely; do not rank yet; do not narrow onto the first scary
thing. Breadth here is the point.

## 5. Turn the lens on yourself
"Assume that list is itself biased. What did I over-weight? What whole area did
I skip? What would a fair reviewer say I got wrong?" Reconcile into one list.
This catches the over-narrowing a premortem alone can still produce.

## 6. Ground, gate, and rank each finding (the calibration)
Keep a finding ONLY if you can give all four. If you can't, it's not a finding:
- **(a) Trigger** — the concrete path: position/precondition → steps →
  observable bad outcome. Can't show it → label it a **"hypothesis to
  investigate,"** not a finding. No free-floating "this could be bad."
  *Exception:* a **whole-system / adjacent-system** risk with a clear mechanism
  (e.g. "this writes to the queue every other feature shares") is a **real
  finding** — tag it **"confirm at scale"**; do NOT demote it to a hypothesis
  just because you lack the load numbers to quantify it. Under-rating the
  blast-radius findings is how the review slips back into tunnel vision.
- **(b) Violated goal** — which stated goal/expectation from step 1 it breaks.
  Violates none → it's out of scope (taste, not a defect). Drop it.
- **(c) Severity × likelihood** in *this* context — High / Medium / Low (not
  false-precision numeric scores), gated by **blast radius** (does the path
  reach something critical?).
- **(d) A fix** — one concrete mitigation, or an explicit "accept / defer
  because ___." A finding with no path to resolution is noise.

Then **rank and bound**: present the few that matter, routed
**Block → This-sprint → Backlog → Hypothesis.** Don't ship a wall of mixed
severities; a list of twelve mediums hides the one critical.

**Sharpen here, don't soften:** if the artifact touches **authentication,
sessions, cryptography, payments, privilege/permissions, or any trust
boundary**, *lower* the bar to flag and raise scrutiny — under-flagging on these
paths is the catastrophic error, and calibration does not mean going easy here.

## 7. Reintegrate and deliver one verdict
Step back to the whole system: does the finding set, taken together, tell the
*true* story of this thing's risk? Any high-impact area unrepresented? Any sign
you fixated on one threat? Then commit to **one verdict**:
**sound · sound-but-needs-these-changes · unsound** — with the 1–3 things that
would move it. Put your step-1 reflex beside the verdict so the human sees what
the review actually changed. Then stop for the human.

## Deliberately not in here (kept lean on purpose)
Full DREAD 1–10 scoring (false precision — use H/M/L), MITRE/PASTA full matrices
and ACH (security-program tooling, not a review warm-up), multi-model ensembles
and formal rules-of-engagement (infrastructure, not a loadable discipline). If a
review genuinely needs those, it's bigger than a crucible.

---

## Related skills (ANAPANA family)
CRUCIBLE reviews; the siblings pick up when the review points at a different kind of work.

| When the review… | Load this skill | Direction |
|---|---|---|
| Concludes "now build/act on the fix" | **`satori`** | CRUCIBLE → SATORI |
| Hits tests that pass but may not bite | **`touchstone`** | CRUCIBLE → TOUCHSTONE |
| Concludes the test suite must be rebuilt | **`whetstone`** | CRUCIBLE → WHETSTONE |
| Happens inside a long/looped session | **`lianxi`** | LIANXI runs CRUCIBLE-lite each iteration |

**How to invoke a sibling:** a human types the slash command (`/satori`, `/touchstone`, `/whetstone`, `/lianxi`). An agent mid-task hands off by loading the sibling skill by name, or by reading that skill's `SKILL.md` in the same skills directory. CRUCIBLE also runs standalone as a one-off review.
