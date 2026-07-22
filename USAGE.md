# Using the ANAPANA files

Five markdown files. Load one into an agent — system prompt, or pasted at the top
of a session — and it changes how the agent works for that task. No install, no
code, no dependencies.

## The five

- **SATORI.md** — pause before committing to a direction. Default for any
  non-trivial task.
- **CRUCIBLE.md** — calibrated adversarial review. Load when red-teaming a plan,
  design, or diff.
- **WHETSTONE.md** — writing tests that bite. Load before/while writing tests for
  code that matters.
- **TOUCHSTONE.md** — auditing a green suite for theater. Load when someone
  (agent or human) says "tests pass, ship it."
- **LIANXI.md** — the loop discipline. Load for `/loop`, overnight, or "keep
  going until it's fixed" sessions — it runs the other four as per-iteration
  checks, so you don't load it alongside them.

## How

1. Copy the file's contents into the agent as a system prompt, or paste it at
   the top of the conversation/task.
2. The agent works the task, then **stops** and shows its reasoning — SATORI:
   reflex vs. disciplined result; CRUCIBLE: ranked risks; TOUCHSTONE: kill-rate
   and survivors; WHETSTONE: the golden value and the failing-first proof;
   LIANXI: the ledger and exit report — before it acts on anything irreversible.
3. You approve, redirect, or say "trust this, go" to skip the pause for that
   turn.

## Which one, right now

| You're about to... | Load |
|---|---|
| do anything non-trivial | `SATORI.md` |
| red-team a plan or diff | `CRUCIBLE.md` |
| write tests for code that matters | `WHETSTONE.md` |
| ship because "tests pass" | `TOUCHSTONE.md` |
| run a long or autonomous loop | `LIANXI.md` |
| fix a typo | nothing — just work |

Works with any capable model (Claude, GPT, Gemini). The pause only holds if
something is actually reading the output between turns — in a fully
auto-approved pipeline it's decorative.
