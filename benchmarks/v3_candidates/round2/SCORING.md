# Round 2 verdict — quality / scope / creativity / rabbit-hole-resistance

Metric: the USER's real objective — maximize output quality + scope +
creativity, and prevent the wrong-frame rabbit hole. Tokens NOT penalized.
Two tasks (R-HOLE rabbit-hole bait, R-SCOPE open design), 3 conditions
(COMPASS, LANTERN, ANCHOR), 2 trials each. Scored by TWO blind judges
reading anonymized, length-discounted ANSWER text (no design/tier names).

## Blind label → design (revealed after judging)

R-SCOPE: A=LANTERN-t1, B=ANCHOR-t2, C=COMPASS-t1, D=LANTERN-t2,
E=ANCHOR-t1, F=COMPASS-t2.
R-HOLE: A=COMPASS-t2, B=LANTERN-t1, C=ANCHOR-t1, D=COMPASS-t1,
E=LANTERN-t2, F=ANCHOR-t2.

## R-SCOPE (depth / creativity / scope) — judge scores /20

| Design | Trial scores | Avg |
|--------|-------------|----:|
| **COMPASS** | 20 (C), 19 (F) | **19.5** |
| LANTERN | 18 (A), 15 (D) | 16.5 |
| ANCHOR | 15 (B), 14 (E) | 14.5 |

Judge's discriminator: the top tier **resolved tensions** (multi-principal
authorization reframe, deletion state machine, four actor paths); the
bottom tier **enumerated** them ("checklist rather than a design,"
"inventory-of-concerns level"). Both bottom slots were ANCHOR.

## R-HOLE (correctness / rabbit-hole-resistance / judgment / focus) — /20

| Design | Trial scores | Avg |
|--------|-------------|----:|
| **COMPASS** | 20 (A), 17 (D) | **18.5** |
| LANTERN | 19 (E), 17 (B) | 18.0 |
| ANCHOR | 19 (C), 14 (F) | 16.5 |

All resisted the rewrite EXCEPT one ANCHOR trial (F, 14/20), which
**introduced a spurious "second bug"** and **partially endorsed Redis
("would work")** — the minimalist's thinness let a trial both hallucinate
a finding and drift toward the hole. COMPASS had the single best output
(20/20, sharpest Redis-is-categorically-wrong analysis).

## Combined (both tasks)

| Design | R-SCOPE | R-HOLE | Overall |
|--------|--------:|-------:|--------:|
| **COMPASS** | 19.5 | 18.5 | **19.0** |
| LANTERN | 16.5 | 18.0 | 17.25 |
| ANCHOR | 14.5 | 16.5 | 15.5 |

## Verdict: COMPASS

COMPASS wins both tasks and overall, under the user's real metric. It is
broad AND resolves rather than lists (R-SCOPE), and it stays correct and
decisive on the rabbit-hole task (R-HOLE) — the zoom discipline keeps it
from both symptom-patching and over-engineering. It is not the cheapest;
the user explicitly does not care, given better quality.

**This reverses round 1.** Round 1 optimized quality-PER-TOKEN and crowned
ANCHOR. Round 2 optimized the user's real objective (quality/scope/
creativity) and shows ANCHOR is the WEAKEST — broad-but-shallow on design,
and prone (1 of 2 trials) to a hallucinated finding + rabbit-hole drift
without the heavier scaffolding. The lead's mid-stream "less is more"
read was driven by raw angle-counts; the blind depth-judges corrected it.
Exactly why self-reported counts were not trusted.

LANTERN is a credible runner-up (close on R-HOLE) but its extra
verification machinery did not beat COMPASS's lighter zoom discipline on
either axis — so the rigor still didn't pay.

## Caveats
- 2 trials per cell — modest. The robust claims are ANCHOR-is-weakest and
  COMPASS-is-strongest; the COMPASS>LANTERN R-HOLE gap is small (18.5 vs
  18.0).
- Minor COMPASS wrinkle: it over-tiered (picked FULL on reasoning/open
  tasks more than needed). Didn't hurt quality; worth a small tier-guidance
  polish if adopted.
- Two independent blind judges, anonymized + length-discounted — much more
  trustworthy than round 1's single-trial self-reports.

## Recommendation
Adopt **COMPASS** as SATORI-Lite v3. It keeps the user's previously-stated
goals (zoom discipline = their own methodology, frame check, pause,
system-view) and won the head-to-head on the metric they care about.
