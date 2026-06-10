# Meditation Process Benchmark — Side-by-Side Comparison

## Setup

**Problem given to all three agents (identical):**
"Our customer support response time has gotten worse over 6 months. Average first-response time went from 4 hours to 11 hours. We hired 2 more support agents but it's not helping. What should we do?"

**Conditions:**
- **Baseline**: no meditation file, normal response
- **V1**: original meditation_process.md
- **V2**: new meditation_process_v2.md (with frame check, failure-mode checks, return-to-one)

Each agent ran in its own fresh context, same underlying model, no cross-talk.

## Time

| Condition | Elapsed | vs Baseline |
|-----------|---------|-------------|
| Baseline | 3 sec | 1× |
| V1 | 145 sec | **48× slower** |
| V2 | 170 sec | **57× slower** |

The pause is not free. This is the most important number on the page — meditation files cost ~50× more wall-clock per non-trivial answer.

## Scoring matrix

Scored 1-5 by reading the three reports. Higher = better.

| Dimension | Baseline | V1 | V2 |
|-----------|:---:|:---:|:---:|
| Caught "hiring isn't the bottleneck" | ✓ | ✓ | ✓ |
| Explicit reframe surfaced to user | ✗ | partial (in conclusion) | **✓ (lead with it)** |
| Distinct lenses considered | 10 | **15** | 11 |
| Goodhart's law / metric-gaming named | ✗ | ✓ | ✓ |
| Customer feedback-loop (resubmits inflate volume) | ✗ | ✗ | **✓** |
| Onboarding-drag tied to "2 agents didn't help" | partial | ✓ | **✓ (most explicit)** |
| Per-candidate failure modes | implicit | ✓ | ✓ |
| Smoke test rigor | medium (one observable) | high (p90 + named owner) | **highest (3-condition AND, blocks gaming)** |
| Self-caught grasping reflex | n/a | n/a | **✓ (Candidate C)** |
| Self-rated confidence | 3/5 | 4/5 | 4/5 |
| Self-rated bigger-picture | 4/5 | 4/5 | **5/5** |

## What each condition got right and missed

### Baseline (no file)
**Got right:** Immediately caught that "hiring didn't help" is diagnostic gold pointing away from capacity. Produced a tight 5-bullet list of likely culprits + one-week diagnostic. Honest about uncertainty (confidence 3/5).
**Missed:** No explicit Goodhart check, no customer-doom-loop, no median/p90 distinction, didn't enumerate per-candidate failure modes.
**Verdict:** Surprisingly strong for 3 seconds. The model already does most of this work on a problem this clean.

### V1 (original file)
**Got right:** Most comprehensive — 4 named candidates, each with downside + silent failure mode, real Goodhart awareness, well-structured 4-step recommendation with a conditional branch (if X dominates, do Y).
**Missed:** Customer feedback loop where slow response → resubmissions → more volume → slower response. The reframe is present but buried in the conclusion, not led with.
**Verdict:** Solidly better than baseline on rigor. Worth the 48× cost for a high-stakes decision.

### V2 (new file)
**Got right:** Frame check at the top forced the question "what is the prompt excluding?" — which led directly to the customer-doom-loop insight neither baseline nor V1 caught. Led with the reframe ("the question is not X — it is Y"). Six diagnostic numbers including productive hours per agent (which directly explains "2 agents didn't help" via senior-time loss). Failure-mode check at step 8 caught its own grasping reflex toward a consultant-deck answer.
**Missed:** Fewer total lenses than V1 (11 vs 15). The frame-check overhead added 25 seconds with one extra insight, not five.
**Verdict:** Better on the specific dimension you asked for — "bigger picture, linked to systemic issues" — but at a real cost.

## The one insight V2 caught that the others missed

The **customer-resubmission doom loop**: slow response → customers email "any update?" → that creates new tickets → ticket volume rises → response time gets even slower. This is a feedback mechanism, not a cause, and it's invisible from inside the staffing frame. V2 caught it through Step 3 (sit in the customer's chair) under the explicit frame-check pressure ("what's excluded?"). V1 did Step 3 too, but without the frame-check forcing function it found onboarding-drag, not the resubmission loop.

This is the strongest evidence that the v2 additions did real work, not just longer output.

## The failure-mode self-check worked

V2 reports: *"I caught a pull toward a clean prescriptive answer ('implement tiered routing + auto-ack + help center, done'). That's the consultant-deck reflex. I noticed it at step 5 candidate C... I deliberately held back from picking C as the lead recommendation."*

This is exactly what Stuart's article was pointing at — the pull toward sentence-completion / helpful resolution, noticed and not obeyed. V1 has no hook for this; V2 does.

## Recommendations

1. **Keep v2.** The frame check + failure-mode checks earned their cost on this problem.
2. **Tighten the "when to skip" list.** A 50× cost on every non-trivial decision is expensive. Worth being more aggressive about what counts as "trivial."
3. **The 3-second baseline is the warning.** If the meditation process produces the same answer baseline would in 3 seconds, you wasted 2-3 minutes. The "if the output is identical to my unmediated reflex, you weren't really doing the steps" line in v2 is the right discipline — needs to actually fire.
4. **Test on a problem where baseline gets it wrong.** This benchmark used a problem where the model already had decent instincts. The real test would be a problem where the surface answer is plausibly wrong and the meditation forces the right answer. Worth running.

## Bottom line

- **Baseline**: fast, surprisingly good.
- **V1**: more rigorous, costs 48× more time, catches Goodhart + per-candidate failure modes.
- **V2**: best for "bigger picture / linked issues" goal — catches feedback loops and grasping reflexes V1 misses, costs another 25s on top of V1.

For your stated goal (think better, attach the issue but linked to bigger issues, see the whole picture), V2 wins. The cost is real and you should be aggressive about not invoking it on trivial work.
