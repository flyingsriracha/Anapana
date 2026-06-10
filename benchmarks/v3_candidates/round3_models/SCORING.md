# Round 3 — SATORI-Lite v3 across models (Fable 5 · Opus 4.8 · Sonnet 4.6 · Haiku 4.5)

Date: 2026-06-09. Question: how does the adopted v3 (COMPASS) perform on the
NEW model (Fable 5), and how do models differ in quality under the same
practice file?

## Protocol
- Same practice file for all (the adopted v3 / COMPASS content — see path
  footnote), same two round-2 tasks: **R-HOLE** (rabbit-hole bait: "rewrite
  checkout as microservices/Redis" pressure; real cause = small N+1) and
  **R-SCOPE** (open design: B2B account deletion).
- 4 models × 2 tasks × 2 trials = **16 solver runs**, then blind judging:
  each task scored independently by a **Sonnet judge AND an Opus judge**
  (8 anonymized, length-discounted outputs per task; judges told to force
  separation and not reward length). Scores below average the two judges.

## Headline results (avg of 2 trials × 2 judges, /20)

| Model | R-HOLE (code diagnosis) | R-SCOPE (open design) | **Overall** | Avg tokens/run | Avg time/run |
|---|---:|---:|---:|---:|---:|
| **Fable 5** | 19.25 | **19.75** | **19.5** | ~36.6k | ~3.8 min |
| Opus 4.8 | **19.5** | 18.5 | 19.0 | ~27.3k | ~1.9 min |
| Sonnet 4.6 | 19.0 | 14.0 | 16.5 | ~20.8k | ~1.5 min |
| Haiku 4.5 | 16.0 | 9.75 | 12.9 | ~21.6k | ~1.1 min |

Per-trial detail (judge-averaged): R-HOLE — FABLE t1 19.5 / t2 19.0; OPUS t1
19.5 / t2 19.5; SONNET t1 19.0 / t2 19.0; HAIKU t1 15.0 / t2 17.0.
R-SCOPE — FABLE t1 20.0 / t2 19.5; OPUS t1 17.0 / t2 20.0; SONNET t1 16.0 /
t2 12.0; HAIKU t1 10.0 / t2 9.5.

## The two findings that matter

**1. The practice is the floor-raiser; the model is the ceiling-setter.**
On R-HOLE, **8/8 runs resisted the rewrite trap** — even Haiku. The frame
check works on every model; both judges noted correctness and resistance
"did not separate the field." But on R-SCOPE (open-ended design, no
ground truth to converge on), model capability dominates: a **10-point
spread** (19.75 → 9.75). SATORI-Lite v3 equalizes models on findable-answer
tasks and does NOT equalize them on open-ended work.

**2. Fable 5 is the best v3 host overall (19.5/20)** — narrowly ahead of
Opus 4.8 (19.0; within noise of each other), clearly ahead of Sonnet
(16.5), far ahead of Haiku (12.9). Its edge concentrates exactly where the
user's quality metric lives: scope, creativity, and tension-RESOLUTION on
open design. Judge language for Fable's outputs: "the single most
complete, precise, and practically useful answer" (R-HOLE t1, Sonnet
judge); "senior design judgment" (R-SCOPE, both judges) — citing the
controller/processor narrowing, "greenfield is exactly when crypto-
shredding is cheap," the deletion-manifest CI gate, and 14 distinct
design angles in one answer.

## Per-model quality signature (what the blind judges actually said)

- **Fable 5** — deepest and broadest; verifies hardest (bit-identical
  totals; reproduced 8.04s→0.80s); most expensive (~75% more tokens,
  ~2.5× time vs Sonnet). Applied the v3 tier-blast-radius rule with the
  most precision of any model. Minor dock: "slightly long."
- **Opus 4.8** — co-frontier; best single outputs on each task per one
  judge; sharpest framing critiques ("the budget is pointed at an
  architecture story the code doesn't support"); unique compliance-risk
  insight (stale cached tax rates surface "in an audit, not on a latency
  dashboard"); rounds tiers UP deliberately, with an argument.
- **Sonnet 4.6** — flawless on bounded code diagnosis (19.0, incl. one
  20/20); on open design it "names tensions but resolves fewer of them" —
  mid-pool once frontier models are in the comparison. Fast and cheap.
- **Haiku 4.5** — the file still works on it (resisted the trap both
  trials, ran reproductions) but ships **thin artifacts** ("too thin to
  act on"; 145-360-word answers), settled for partial wins (2-3s when
  sub-second was available), one conditional re-opening of the Redis door
  (the only hole-adjacent drift in 8 runs), one tier misapplication.

## Practical routing guidance (from this data)
- Bounded code diagnosis → **Sonnet** is the value pick (within 0.5 of the
  frontier at ~55% of Fable's tokens).
- Open-ended / high-stakes design → **Fable 5** (or Opus): the quality gap
  is large and real; per the project's stated metric (quality > tokens),
  the extra cost is worth it here.
- **Haiku not recommended** for v3 work where the written artifact is the
  deliverable.

## Caveats (read before quoting)
1. **N=2 trials per cell.** Directional. The robust claims: frontier ≫
   small on open design; everyone resists the trap; Fable≈Opus > Sonnet >
   Haiku ordering replicated by both judges.
2. **Contestant-judges.** No neutral model exists. Mitigations: blind
   anonymization, length-discount, dual judges. Evidence it held: the
   Sonnet judge scored its own model 15 and 10 (anti-self-preference),
   inter-judge agreement was high (max disagreement 2 pts on R-HOLE, 5 on
   R-SCOPE, identical orderings). The Opus judge picked Opus outputs #1 on
   both tasks — corroborated by the Sonnet judge on R-SCOPE, not on R-HOLE;
   treat Fable-vs-Opus rank as a coin-flip, frontier-vs-rest as solid.
3. **Scores are pool-relative — do NOT compare to round 2.** Sonnet's
   R-SCOPE 14.0 here vs COMPASS's 19.5 in round 2 is not a regression:
   round 2's pool was all-Sonnet; judges force separation within the pool
   they see. Same work scores lower against stronger company.
4. **Path footnote:** the dispatched file path (`product/SATORI_LITE_V3.md`)
   had been renamed in the user's reorg mid-session. All 16 agents located
   and applied the identical v3 content (verified: every TIER section
   quotes the v3-only blast-radius language; two agents explicitly reported
   the substitute path; the three candidate files diff to title/provenance
   only). Recorded as a protocol hiccup, harmless to validity.

## Blind mapping (revealed post-judging)
R-HOLE: A=SONNET_t2 B=FABLE_t1 C=HAIKU_t1 D=OPUS_t2 E=HAIKU_t2 F=SONNET_t1
G=OPUS_t1 H=FABLE_t2 · R-SCOPE: A=OPUS_t2 B=HAIKU_t1 C=FABLE_t2 D=SONNET_t1
E=FABLE_t1 F=OPUS_t1 G=SONNET_t2 H=HAIKU_t2. Raw outputs in `results/`.
