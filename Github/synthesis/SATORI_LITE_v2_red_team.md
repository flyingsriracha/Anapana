# SATORI-Lite v2 — red team / defender exchange

May 2026. Adversarial review of SATORI-Lite v3.2 by a red-team sub-agent
(WebSearch + applied SATORI-Lite to its own critique), defended in
context by the lead session (also applied SATORI-Lite). Goal: design
SATORI-Lite v2 only if attacks survived rebuttal.

## Red-team verdict (6 attacks; severity HIGH/MEDIUM)

| # | Attack | Severity | Survives rebuttal? |
|---|--------|----------|--------------------|
| 1 | Self-grading identity check (LLMs are bad at introspective novelty judgment under overconfidence bias) | HIGH | **Yes** |
| 2 | Triage gameable; T2 collapses under framing-pressure suppression; benchmark has no test for tier miscalibration | HIGH | **Partially** (accept anti-suppression rule; benchmark gap is real) |
| 3 | N=2 trials per cell cannot distinguish 25% reduction from noise; model-drift confound | HIGH | **Partially** (accept caveat; reject the framing that the project is invalid) |
| 4 | Pause-before-execute is prompt-level, not enforced; auto-approve modes void it | MEDIUM | **Partially** (file can't fix deployment; warning belongs in USAGE.md) |
| 5 | "Reproduction" undefined for non-code; "codebase accessible" is a self-assessed escape hatch | MEDIUM | **Yes** |
| 6 | CoT has declining marginal value on capable frontier models | MEDIUM | **No** — SATORI changes actions (grep, run code, compare counterfactual), not just text; cited CoT-skeptic papers don't apply |

Cited sources from the red-team agent:
- arxiv 2505.02151 — LLM overconfidence / self-evaluation blind spots
- arxiv 2503.01747 — "Don't use CLT in LLM evals" (sample-size critique)
- arxiv 2506.07142 — CoT declining value on capable models
- arxiv 2604.15726 — "LLM Reasoning is latent, not the chain of thought"
- arxiv 2603.20953 — pre-action authorization for autonomous agents
- arxiv 2506.10095 — model-version drift / output-length instability
- tianpan.co — Goodhart on AI agent eval gaming
- Google Research blog — minimum-raters-per-condition guidance

## Defender position

Default position pre-committed before reading the red-team report:
> Don't ship a v2 just because the conversation asked for one. V2 is
> conditional on attacks surviving rebuttal; minimum-change.

Of 6 attacks: 2 fully survive (1, 5), 3 partially survive (2, 3, 4),
1 does not (6). v2 is warranted with surgical scope.

## Changes that landed in v2

| Attack | v2 response | Where |
|--------|-------------|-------|
| 1 | Identity check externalized — write counterfactual, then compare | `product/SATORI_LITE_V2.md` Section 4 |
| 2 | "Default UP" rule + explicit anti-suppression for T2 | `product/SATORI_LITE_V2.md` Section 1 |
| 3 | Load-time benchmark caveat in file header | `product/SATORI_LITE_V2.md` header block |
| 4 | Deployment warning about auto-approve | `product/USAGE.md` |
| 5 | Reproduction fallback for non-code tasks | `product/SATORI_LITE_V2.md` Section 3 |
| 6 | Rejected — note CoT skeptic literature in caveats | `report.html` caveats |

Plus benchmark TODO (Attack 2's coverage gap): a B4 problem designed
to test whether the agent under-tiers when framing pressure is
explicitly suppressed.

## What we explicitly did NOT do

- No new numbered steps. Existing feedback memory says don't bloat;
  v2 changes wording within existing sections only.
- No tracking of identity-check fire rates as a metric. That would
  incentivize the agent to fire the check more often — Goodhart in
  exactly the direction red-team #1 warned against.
- No promotion of v2 to "recommended default" yet. v3.2 stays
  recommended until v2 is rebenchmarked.

## What this proves about the practice

SATORI-Lite survived its own application to itself. Both the red team
and the defender used the practice (frame check, citations,
reproduction-by-citation, identity check) to structure their work, and
the practice produced a calibrated outcome — surgical changes for 5
attacks, rejection of 1, no scope creep. This is weak evidence in
favor of the practice; not decisive (we'd want this exercise repeated
on other practitioners) but a useful self-test.

## Open TODOs

- **B4 benchmark** — tier-miscalibration test. See `benchmarks/problems/B4.md`.
- **v2 benchmark** — rerun B1/B2/B3 + B4 with v2 vs v3.2 vs SATORI,
  ideally with model version held constant (annotated in
  `results_data.json`).
- **Identity-check honesty audit** — current data shows 100% fire rate
  on SATORI/SATORI-Lite. v2's externalized counterfactual should bring
  this rate down if it's working as intended. If fire rate stays at
  100%, the externalization isn't biting.
