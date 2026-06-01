# How to use the ANAPANA practice files

There are four files in this folder:

- `BREATH.md` — Stage 01. The 8-step pause.
- `INSIGHT.md` — Stage 02. BREATH + frame check.
- `SATORI.md` — Stage 03. INSIGHT + reproduction + identity check + time budget.
- `SATORI_LITE.md` — Stage 03 (lean variant). Triage + tiered depth + mandatory reproduction. Recommended default.

Each stage subsumes the previous. **You only need one file at a time** — the one
matching the depth of practice you want the agent to follow. Start with
SATORI-Lite unless you have a specific reason to fall back.

---

## ⛔ Pause-before-execute (built into every file)

Every ANAPANA file tells the agent to produce its analysis and proposed
fix as **text only**, then STOP and wait for your explicit approval
before editing files, running state-changing commands, or applying any
fix. This is non-negotiable — the entire point of the practice is to
let you inspect the chain of reasoning before action.

If you want the agent to skip the pause for a particular turn (e.g.
"I trust this, go ahead and apply it"), say so explicitly in that turn.
The default is always present-and-stop.

If you find the agent acting before you approve, the file isn't being
followed. Re-paste it more prominently or move it from prefix to system
prompt.

---

## Quick start — Claude (claude.ai, Claude Code, API)

**Option A — System prompt (recommended for sustained use):**
Paste the contents of `SATORI.md` as the system prompt or "custom instructions"
for the conversation. The agent applies it to every non-trivial task.

**Option B — Per-message prefix (for one-off tasks):**
```
Read and follow the meditation process below for this task.

[paste contents of SATORI.md]

---

[your actual question or bug report]
```

**Option C — Claude Code (file reference):**
Place the file at `.claude/meditation.md` and reference it in `CLAUDE.md`:
```
For non-trivial decisions, read and follow .claude/meditation.md before acting.
```

---

## Quick start — Other LLMs

**GPT (ChatGPT, API):** Use Option A or B above. GPT-4 and later respond well
to the structured checklist format. Smaller models may skip steps.

**Gemini:** Use Option B (per-message prefix). Gemini's system instructions
sometimes get truncated; inlining the file is more reliable.

**Open-weight models (Llama, Mistral, etc.):** Use Option B. For models below
~70B params, simplify to BREATH or write a shorter custom variant — the eight
steps will be skimmed if the file is long.

---

## Which file to use?

| Situation | File |
|-----------|------|
| First time trying ANAPANA, want minimum overhead | **BREATH** |
| Prompts often feel narrow or pressured, need reframing | **INSIGHT** |
| Multi-file changes, hidden-dependency work, high stakes | **SATORI** |
| Pure-reasoning Q&A where surface answer might be wrong | **INSIGHT** or **SATORI** |
| Simple typos, lint, one-line fixes | **None** (the agent should skip the practice) |

---

## What to expect

The agent will:
1. Take longer to respond. SATORI averages 30 seconds–3 minutes longer than
   the unmediated answer, depending on task complexity.
2. Spend more tokens — but typically only 0–30% more on code tasks (most of
   the cost is already reading the code).
3. Produce a response that shows the work — frame check, citations, alternatives
   considered, reproduction output.
4. Sometimes refuse to give the answer you asked for and propose a reframe
   instead. This is the practice working, not failing.

---

## How to tell if it's working

After 10–20 invocations, look at your agent's outputs and ask:

- **Identity check:** is the answer noticeably different from what an unmediated
  agent would have produced? (SATORI's own checklist asks this.)
- **Hidden-issue rate:** how often does the agent surface issues you didn't
  ask about, that turn out to be real?
- **Rework rate:** how often do agent-shipped changes need to be reverted or
  patched within a week?

If the identity check rarely fires "different from reflex," the agent is
treating the practice as ritual. Consider whether you're applying it to tasks
that are too simple. See the "When to skip" section in each file.

---

## See also

- `../report.html` — interactive benchmark report with the evidence behind these
  recommendations
- `../benchmarks/methodology.md` — full replication protocol
- `../README.md` — folder overview
