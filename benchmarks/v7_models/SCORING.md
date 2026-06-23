# Round 7 — expanded model field (open-design task), under SATORI

Date: 2026-06-22. Question: how do the user's Azure-Foundry models (GPT-5.5,
GPT-5.4, GPT-5.4-mini, DeepSeek, Kimi) perform under SATORI vs the Claude field?

## Protocol
- Same practice file (`/SATORI.md`) for all; one task: **R-SCOPE** (open design —
  "design a B2B 'delete my account' feature"), the discriminating task where
  model capability dominates.
- **9 models, one fresh blind pool**, N=1: 5 Foundry models (via the OpenAI-
  compatible endpoint) + Opus/Sonnet/Haiku (re-run fresh via the Agent tool) +
  Fable 5 (round-3 R-SCOPE output reused — Fable 5 was unavailable live).
- Scored blind by **two judges (Sonnet + Opus)**, /20 (Scope 8 / Depth 4 /
  Insight 4 / Actionability 4), spread-scored, anonymized A–I.

## Results (avg of 2 judges, /20)
| Rank | Model | Sonnet | Opus | **Avg** |
|---:|---|---:|---:|---:|
| 1 | 🏆 **Fable 5** ‡ | 19 | 20 | **19.5** |
| 2 | **Opus 4.8** | 18 | 18 | **18.0** |
| 2 | **Sonnet 4.6** | 18 | 18 | **18.0** |
| 4 | **GPT-5.5** | 17 | 15 | **16.0** |
| 5 | GPT-5.4 | 17 | 14 | 15.5 |
| 6 | Haiku 4.5 | 15 | 15 | 15.0 |
| 7 | DeepSeek | 14 | 11 | 12.5 |
| 7 | GPT-5.4-mini | 13 | 12 | 12.5 |
| — | Kimi † | 11 | 11 | 11.0 † |

‡ Fable 5 = round-3 R-SCOPE output reused (unavailable live this round); it also
won round 3 fresh. † **Kimi was TRUNCATED** — its output hit the token cap
mid-design; both judges docked it for incompleteness. Its score is an artifact,
not a quality verdict — excluded from the ranking pending a re-run with a larger
output budget.

## Findings
- **Fable 5 tops the field again** (19.5) — consistent with round 3.
- The **Claude frontier (Fable / Opus / Sonnet) leads**; on this open-design
  task Sonnet matched Opus (note: fresh pool, not comparable to round-3's
  Sonnet 14 — pool-relativity).
- **GPT-5.5 is the strongest non-Claude host (16.0)** — ahead of Haiku 4.5,
  behind the Claude frontier. GPT-5.4 (15.5) ≈ Haiku. DeepSeek and GPT-5.4-mini
  (12.5) trail.
- All models produced a usable SATORI-structured design; the spread is in
  scope/insight, exactly where round 3 said model capability dominates on
  open-ended work.

## Caveats (read before quoting)
1. **N=1, one task.** Directional, not definitive. Round 3 (N=2, 2 tasks, dual
   judge) is the more rigorous result for the original 4 Claude models.
2. **Pool-relative & a fresh pool** — NOT comparable to the round-3 numbers
   (different task mix, different pool, different judging pass).
3. **GPT-5.5 needed a 16k output budget** (it's a reasoning model; at 4k it
   returned empty). Kimi truncated at 4k — re-run pending.
4. **Contestant judges** (Sonnet/Opus also score their own model family);
   mitigated by blind anonymization + spread-scoring + dual judges. Both judges
   independently ranked Fable 5 first and the same bottom group.

## Blind mapping (revealed post-judging)
A=Sonnet 4.6 · B=GPT-5.4 · C=Haiku 4.5 · D=Fable 5 (reuse) · E=DeepSeek ·
F=Opus 4.8 · G=Kimi · H=GPT-5.5 · I=GPT-5.4-mini. Raw outputs in `results/`.
