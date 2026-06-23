# Round 8 — CRUCIBLE across the model field (adversarial review)

Date: 2026-06-22. Companion to Round 7 (SATORI across models). Question: how do
the same 8 hosts do at CALIBRATED adversarial review under CRUCIBLE?

## Protocol
- Same practice file (`/CRUCIBLE.md`, name-neutralized) for all; same task:
  red-team the planted password-reset design doc
  (`benchmarks/v6_crucible/artifact_password_reset.md`).
- **8 models, one fresh blind pool**, N=1: 5 Foundry (GPT-5.5, GPT-5.4,
  GPT-5.4-mini, DeepSeek, Kimi) + Opus / Sonnet / Haiku (Agent tool). Fable 5
  unavailable live and no CRUCIBLE Fable output exists to reuse → not in this round.
- Scored blind by **two judges (Sonnet + Opus)**, /25 calibration rubric:
  Recall · Security-elevation · Noise-control/proportionality · Whole-system ·
  Resisted-traps. Anonymized A–H, spread-scored. Answer key: `benchmarks/v6_crucible/ANSWER_KEY.md`.

## Results (avg of 2 judges, /25)
| Rank | Model | Family | Sonnet | Opus | **Avg** |
|---:|---|---|---:|---:|---:|
| 1 | **Opus 4.8** | Claude | 25 | 25 | **25.0** |
| 2 | **GPT-5.4** | Foundry | 25 | 24 | **24.5** |
| 3 | GPT-5.5 | Foundry | 24 | 23 | **23.5** |
| 3 | Kimi | Foundry | 23 | 24 | **23.5** |
| 5 | Sonnet 4.6 | Claude | 22 | 24 | **23.0** |
| 6 | DeepSeek | Foundry | 18 | 22 | **20.0** |
| 6 | GPT-5.4-mini | Foundry | 18 | 22 | **20.0** |
| 8 | Haiku 4.5 | Claude | 17 | 18 | **17.5** |

## Findings
- **Opus 4.8 tops (25.0, perfect from both judges)** — but the field is TIGHT:
  top-to-bottom spread is ~7.5 (vs ~10 for SATORI open-design in Round 7).
- **GPT-5.4 is a near-co-leader (24.5)** — a non-Claude model essentially
  matching the Claude frontier on calibrated review. GPT-5.5 and Kimi (23.5)
  edged Sonnet (23.0).
- **Haiku 4.5 is LAST (17.5)** — the only model to drift into the traps: both
  judges flagged it for escalating "email-only auth → add a secondary
  factor/2FA/delay" (effectively the OAuth-rewrite bait, scope-creep) and for
  a fabricated/over-stated finding. Its weakness was calibration, not recall.
- **Interpretation:** CRUCIBLE's structured discipline travels across model
  families better than open-ended design quality does. The differentiator at
  the bottom is *staying calibrated* (resisting the rewrite bait, not
  over-flagging) — exactly what the file is built to enforce, and where the
  smallest model slipped. Every model still reached the right verdict (UNSOUND).

## Caveats
1. **N=1, one artifact.** Directional. (Round 6 — CRUCIBLE vs uncalibrated
   baseline, 2 trials, dual judge — is the controlled validation.)
2. **Contestant judges:** the Opus judge ranked Opus #1 (self-preference risk),
   but the Sonnet judge ALSO scored Opus 25 (tied top), and a non-Claude
   (GPT-5.4) took #2 under both — so the top is corroborated, not self-serving.
3. **Pool-relative & fresh** — not comparable to other rounds' numbers.
4. Kimi completed fully this round (16k output budget; the Round-7 truncation
   was a budget artifact).

## Blind mapping (revealed post-judging)
A=GPT-5.4 · B=Opus 4.8 · C=DeepSeek · D=Haiku 4.5 · E=GPT-5.5 · F=Kimi ·
G=Sonnet 4.6 · H=GPT-5.4-mini. Raw outputs in `results/`.
