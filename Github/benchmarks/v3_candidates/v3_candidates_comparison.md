# SATORI-Lite v3 candidates — pros / cons + bake-off plan

Three named designs by the lead agent, spread across a structure/rigor
spectrum so the benchmark discriminates. Whichever wins becomes
SATORI-Lite v3 (it does not rename the locked BREATH/INSIGHT/SATORI
stages — these are candidate *files* for the v3 slot).

| | ANCHOR | COMPASS | LANTERN |
|---|---|---|---|
| Weight | ~35 lines | ~70 lines | ~95 lines |
| Bet | native reasoning does the rest | balanced re-center | verification rigor pays |
| Identity check | reflex vs proposal (glance) | reflex vs proposal (delta for human) | factored: reflex + open-form verification Qs |
| Reproduction | gate, predict-then-run | gate, mandatory when code reachable | gate + open-form prediction + atomic claims |
| Zoom discipline | — | yes (in trace) | yes (in trace) |
| Tiers | 3 coarse | 4 (SKIP/FAST/STANDARD/FULL) | 4 |

## ANCHOR — minimalist
**Pros:** Lowest token cost; least ritual; hardest to game (almost nothing
to perform); leans on the audit's finding that benefit is subtractive;
fastest to actually follow, so most likely to be USED. **Cons:** May
under-perform on multi-file traps where the dropped trace/grep step was
load-bearing (B3-style hidden consumers); no explicit altitude rule, so
risk of symptom-fixing; thin scaffolding may let weaker models skip the
hard moves.

## COMPASS — balanced re-center
**Pros:** Keeps the trace+grep that caught hidden consumers in prior
benchmarks; embeds the user's zoom discipline (anti symptom-fixing AND
anti over-engineering); tiered depth scales cost to stakes; the "medium
average" the user explicitly favors. **Cons:** Middle-weight means middle
token cost; more surface area to satisfice through; the identity check is
still a single comparison (the research's weaker "joint-ish" form,
mitigated by reflex-first but not fully factored).

## LANTERN — verification-heavy
**Pros:** Implements the one robust, evidence-backed anti-rubber-stamp
mechanism (factored, open-form, context-isolated verification); atomic
claim decomposition makes reproduction auditable; most defensible against
the self-grading critique. **Cons:** Highest token + time cost; most
ritual surface, so highest risk of "performing the verification" without
behavior change; the extra rigor may not pay on simple traps (over-kill
where COMPASS/ANCHOR already get it right); closest to re-importing the
heavy machinery the audit warned against.

## What the bake-off measures
Same protocol as the original benchmark: B1 (reasoning), B2 (code w/
README), B3 (code no README, framing-pressure trap). Conditions:
**SATORI-Lite v2** (never benchmarked) + ANCHOR + COMPASS + LANTERN, all
on one held-constant model (sonnet) so they're comparable to each other.
v3.2's existing numbers stand as a documented reference (different
session/model — not directly comparable, flagged).

Per-cell we record: tier picked, surface-fix correctness, hidden-issue
discovery, reflex→proposal delta (did the practice change the answer?),
reproduction actually run, tokens, time.

**Decision rule (pre-committed):** the winner is the design with the best
quality-per-token on the code benchmarks AND a non-trivial reflex→proposal
delta. If ANCHOR matches the heavier designs on quality, minimalism wins
(less is more). If LANTERN's rigor doesn't beat COMPASS on hidden-issue
discovery, the rigor isn't paying and COMPASS wins. Ties break toward the
lighter design.

Caveat: single trial per code cell on B3 (the high-variance one) is
noisy — a close result triggers a trial-2 follow-up before adopting.
