# Prior art — is ANAPANA reinventing the wheel?

Internet sweep (2026-06-04) for projects that already do what ANAPANA does,
so we lean on existing work where it's solid and only build where there's a
genuine gap. Verdict: **not reinventing the wheel — the integrated,
loadable five-mechanism pre-task discipline (especially the frame-check and
reflex-capture) has no direct equivalent.**

## The closest things that exist

| Project | What it is | Overlap | Gap vs ANAPANA |
|---------|-----------|---------|----------------|
| [SYCOPHANCY.md](https://sycophancy.md/) | Drop-in markdown governance file; anti-sycophancy rules an agent self-monitors | **Closest in format** (loadable markdown discipline) | Single-concern; no frame-check, pause, triage, reproduce-gate, reflex-capture |
| [AGENTS.md](https://agents.md/) (Linux Foundation std, 60k+ repos) | "A README for agents" — project context/commands | Same load-a-markdown pattern | Pure context delivery; zero reasoning ritual |
| [Cursor](https://cursor.com/blog/agent-best-practices) / [Windsurf](https://docs.windsurf.com/plugins/cascade/planning-mode) plan-mode | Agent presents a plan and waits for approval | **Closest to pause-before-execute** | Built into IDE UX, not a file; no frame-check/triage/reproduce/reflex |
| [HumanLayer](https://www.humanlayer.dev/) / [LangGraph interrupt()](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt) | SDK/infra for human approval at the tool-call layer | Human-gatekeeper mechanism | Code infrastructure, not a session-level reasoning discipline |
| [GitHub Spec Kit](https://github.com/github/spec-kit) (90k★) | Spec → Plan → Tasks → Implement workflow | Think-before-code instinct | Project-level workflow; assumes the spec is sound (no frame-check) |
| [obviousworks/agentic-coding-meta-prompt](https://github.com/obviousworks/agentic-coding-meta-prompt) | Mega-prompt with `<cognitive_thought>` + STOP signal | Structured pre-action planning | Assumes the task is correct; no frame-check or human gate |
| [Pre-Commit Review Gate](https://imti.co/pre-commit-review-gate/) | Hook blocks commit until adversarial sub-agent returns CLEAN | Pre-commit enforcement | Post-implementation code review, not pre-task reflection |
| anti-sycophancy ecosystem ([GitHub topic](https://github.com/topics/anti-sycophancy)) | 15+ single-mechanism repos | Anti-sycophancy | None integrate the five mechanisms |

## Technique prior art (what ANAPANA builds on)

- **Reflexion** (arxiv 2303.11366), **Chain-of-Verification** (2309.11495),
  **Self-Refine**, **ReAct**, **Tree of Thoughts**, **Self-Consistency**,
  **Constitutional AI**. All improve *output accuracy on a given task*.
- **None** of them cover: (1) **frame-check / problem-selection** ("is the
  stated task the right task?"), (2) **human-as-gatekeeper pause** (they're
  closed-loop automated), (3) **reflex-capture** (gut answer first, compare
  after). These three are ANAPANA's differentiated mechanisms.

## Verdict

**Already well-covered — lean on / cite, don't rebuild:**
- Human-in-the-loop *infrastructure* → HumanLayer, LangGraph interrupt().
  ANAPANA's pause works at the discipline level (complementary, not novel
  as a concept).
- Post-hoc reflection → Reflexion / Self-Refine / AutoGen.
- Anti-sycophancy → SYCOPHANCY.md + ecosystem (ANAPANA folds it in as one
  ingredient, not a standalone file).
- Spec-before-code → GitHub Spec Kit.

**Genuinely novel / underserved — worth continuing:**
1. **Frame-check as a formalized mandatory pre-task step.** No academic or
   productized analog found.
2. **The integrated five-mechanism discipline as one loadable markdown**
   (frame-check + pause + triage + reproduce-gate + reflex-capture). The
   combination + the delivery format is the gap.
3. **Reflex-capture** (write gut answer first, compare after). No prior
   framework operationalizes this for agents.
4. **Empirical measurement of a reasoning discipline** (blind-judged
   bake-offs on quality/scope/rabbit-hole, not just benchmark accuracy).

**Honest caveats:** the search can't rule out private/very-new repos (the
space moves fast — AGENTS.md went 0→60k repos in under a year). And the
[Pre-Commit Review Gate writeup](https://imti.co/pre-commit-review-gate/)
warns that in-context checklists often fail because "agents treat them as a
vibe-check" — ANAPANA's hedge against that is exactly its benchmarking +
the pause-before-execute contract (the human, not the checklist, is the
enforcement). Keep accumulating multi-trial evidence.
