# ANAPANA Skills

Five pre-commit **cognitive disciplines** for AI coding agents, packaged as
[Agent Skills](https://agentskills.io/) so they install into Claude Code, OpenAI
Codex, and any other agent that reads the `SKILL.md` standard. Each is a
self-contained one-off skill; together they form a cycle where one skill can
hand off to the next.

> ANAPANA (from *anapanasati*, mindfulness of breathing): the agent pauses and
> reflects **before** it commits to an answer, instead of reflexively acting.

## The five skills

| Skill | Discipline | Load it when… |
|---|---|---|
| **satori** | The Pause — frame before acting | You're about to build, change, or decide something where being wrong is costly |
| **crucible** | Adversarial review | You're reviewing a plan, design, PR, or change for flaws |
| **whetstone** | Writing tests that bite | You're writing tests (especially for code you also wrote) |
| **touchstone** | Test-rigor audit | You need to know whether an existing test suite can be trusted |
| **lianxi** (练习) | The loop | You're running a long/autonomous/overnight loop — it orchestrates the other four |

## How the skills work together (for the LLM)

Each `SKILL.md` contains an **"ANAPANA family"** callout near the top and a
**"Related skills"** table at the end that tell the agent when to hand off to a
sibling. The handoff graph:

```
                       ┌─────────────┐
                       │   SATORI    │  frame / decide / build
                       │  (the pause)│
                       └──────┬──────┘
              reviewing? ─────┼───── writing tests?
                 │            │            │
                 ▼            │            ▼
          ┌─────────────┐     │     ┌─────────────┐   step 9   ┌─────────────┐
          │  CRUCIBLE   │     │     │  WHETSTONE  │ ─────────► │ TOUCHSTONE  │
          │  (review)   │     │     │(write tests)│ ◄───────── │(trust tests)│
          └─────────────┘     │     └─────────────┘  theater?  └─────────────┘
                              │       rebuild
                       ┌──────┴──────┐
                       │   LIANXI    │  runs all four as per-iteration kernels
                       │  (the loop) │  + memory across iterations (LEDGER.md)
                       └─────────────┘
```

Key handoffs, all written into the skill bodies so the agent follows them
automatically:

- **satori → crucible / whetstone / touchstone / lianxi** — if the framed task
  is really a review, a test-writing job, a test audit, or a long loop.
- **whetstone → touchstone** — mandatory step 9: after writing a suite, run an
  independent audit (a different pass than the one that wrote the tests).
- **touchstone → whetstone** — if the audit reveals theater, rebuild the suite
  rather than patching the green.
- **crucible → satori / whetstone** — act on findings, or rebuild tests.
- **lianxi ⊃ all four** — the loop runs compressed kernels of each every
  iteration and loads the full sibling skill when one move needs depth.

**How an agent invokes a sibling:** either the skill runtime auto-triggers the
sibling from its `description`, or the agent reads the sibling's `SKILL.md` in
the same skills directory (they are installed side by side). No code, no network,
no dependencies — these are pure instruction skills.

## How a human calls a skill (one-off)

Each skill also stands alone. In an agent that supports slash commands:

```
/satori        # pause and frame before I act
/crucible      # adversarially review this design
/whetstone     # write tests that actually bite
/touchstone    # tell me if these tests can be trusted
/lianxi        # run this as a disciplined loop
```

Or just describe the situation ("review this design", "are these tests any
good?") and the matching skill's `description` will trigger it.

## Install

These are **bare skills** — a folder per skill, each containing a `SKILL.md`.
Install by copying (or symlinking) the folders into your agent's skills
directory. The `install.sh` script does this for you:

```bash
# from this skill/ directory
./install.sh claude     # → ~/.claude/skills/
./install.sh codex      # → ~/.agents/skills/
./install.sh both       # both of the above
./install.sh both --link # symlink instead of copy (edits here propagate live)
```

Or do it manually:

| Agent | Personal (all projects) | Per-project |
|---|---|---|
| **Claude Code** | `~/.claude/skills/<name>/SKILL.md` | `.claude/skills/<name>/SKILL.md` |
| **OpenAI Codex** | `~/.agents/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` |
| **GitHub Copilot / Cursor** | that agent's skills directory | same |

```bash
# manual example, Claude Code, personal scope:
mkdir -p ~/.claude/skills
cp -R satori crucible whetstone touchstone lianxi ~/.claude/skills/
```

Both Claude Code and Codex auto-detect new skills; Codex may need a restart.
The five folder names (`satori`, `crucible`, `whetstone`, `touchstone`,
`lianxi`) must match the `name:` in each `SKILL.md` — don't rename the folders.

## Verify

```bash
# cross-agent validator (agentskills.io)
skills-ref validate ./satori    # repeat per skill

# Claude Code
claude plugin validate .        # if you later wrap these in a plugin
# or, inside a session:
"What skills are available?"    # each of the five should be listed and described
```

## Notes on triggering

These are **process/meta skills** (pure reasoning, no code), so auto-triggering
is fuzzier than for a capability skill like "process PDFs." Two ways to make them
fire more reliably:

1. Invoke explicitly with the slash command when you want the discipline.
2. Add a nudge to your `CLAUDE.md` / `AGENTS.md`, e.g.
   *"Before committing non-trivial changes, use the `satori` skill. When
   reviewing a design, use `crucible`."*

## What these are NOT

No scripts, no API calls, no authentication, no external dependencies. Nothing
runs on your machine — the "skill" is the instruction text the model reads. Safe
to inspect and safe to install.
