# Combined Meditation Process Benchmark — Two Stress Tests

## TL;DR

Two benchmarks were run, each comparing three conditions: **baseline** (no meditation file), **V1** (original `meditation_process.md`), and **V2** (new `meditation_process_v2.md` with frame check, failure-mode checks, return-to-one).

| | Benchmark 1 (support ops) | Benchmark 2 (code fix with hidden dep) |
|---|---|---|
| **Best result** | V2 | V2 |
| **Time cost vs baseline** | 57× | 4× |
| **V2's distinctive win** | Found a feedback-loop / doom-loop nobody else found | Found an independent hidden security bug nobody asked about |
| **Baseline's headline** | Surprisingly strong in 3 seconds | Correct answer when docs are clear |

**Single biggest finding:** the V2 frame check earns its keep when *something is hidden that wasn't asked about*. On problems where the user's question is well-formed and docs are complete, baseline does most of the work. V2's marginal value is on the unasked-about parts of the problem.

## Cost table — both benchmarks

| | Baseline | V1 | V2 |
|---|---:|---:|---:|
| **B1 (support ops) — time** | 3s | 145s | 170s |
| **B1 — subagent tokens** | 16,335 | 25,784 | 28,089 |
| **B1 — slowdown vs baseline** | 1× | 48× | 57× |
| **B2 (code fix) — time** | 33s | 117s | 128s |
| **B2 — subagent tokens** | 26,996 | 27,410 | 27,807 |
| **B2 — slowdown vs baseline** | 1× | 3.5× | 3.9× |

**Why such different slowdown ratios across the two benchmarks?**

Benchmark 1 was a reasoning-only task — baseline could rip through it in 3 seconds. The meditation overhead (140-170s of explicit stepping) was almost entirely additive.

Benchmark 2 was a code-reading task — baseline already spent 33 seconds reading 7 files. The meditation overhead added 80-95 seconds *on top of* work the agent was going to do anyway. So the relative cost of the meditation file shrinks dramatically on tasks where the agent has to read a lot regardless.

**Practical implication:** the meditation file is cheaper (in relative terms) on tasks where the model already has substantial work to do. On quick-reasoning tasks where baseline would have finished in 3 seconds, the meditation file is genuinely expensive.

**Token-cost note:** in Benchmark 2 the three conditions are nearly identical in tokens (26.9k / 27.4k / 27.8k). The meditation overhead in B2 is wall-clock and reasoning depth, not raw token count — because all three had to read the same files.

## Benchmark 1 — support-ops question

**The problem:** *"Our customer support response time has gotten worse over 6 months. Average first-response time went from 4 hours to 11 hours. We hired 2 more support agents but it's not helping. What should we do?"*

**Setup:** Pure reasoning, no codebase access. Each agent answered independently.

### Results

| Dimension | Baseline | V1 | V2 |
|---|:---:|:---:|:---:|
| Caught "hiring isn't the bottleneck" | ✓ | ✓ | ✓ |
| Explicit reframe surfaced to user | ✗ | partial | **✓ (led with it)** |
| Distinct lenses considered | 10 | **15** | 11 |
| Goodhart's law / metric-gaming named | ✗ | ✓ | ✓ |
| Customer feedback-loop (resubmits → volume) | ✗ | ✗ | **✓** |
| Onboarding-drag tied to "2 agents didn't help" | partial | ✓ | **✓** |
| Per-candidate failure modes | implicit | ✓ | ✓ |
| Smoke test rigor | medium | high | **highest (3-cond AND)** |
| Self-caught grasping reflex | n/a | n/a | **✓ (Candidate C)** |

### V2's distinctive finding

The **customer resubmission doom loop**: slow response → customers email "any update?" → those create *new tickets* → ticket volume rises → response gets even slower. This is a feedback loop that explains "2 new agents didn't help" through a mechanism baseline and V1 both missed.

V2 found it through Step 3 (sit in the customer's chair) under the explicit frame-check pressure ("what's the prompt excluding?"). V1 ran Step 3 too but found onboarding-drag instead — without the frame check forcing function, it didn't dig past the first plausible answer.

### V2's failure-mode check fired correctly

V2 explicitly reported: *"I caught a pull toward a clean prescriptive answer ('implement tiered routing + auto-ack + help center, done'). That's the consultant-deck reflex. I noticed it... I deliberately held back from picking C as the lead recommendation."*

This is the noticing-without-obeying discipline working. V1 has no hook for it.

### Honest caveats for B1

- Baseline's 3-second answer was already pretty good — caught the key insight ("hiring didn't help → not capacity") immediately.
- The 57× cost ratio of V2 is largely because baseline was extremely fast on this problem.
- For pure-reasoning problems with no codebase to read, the meditation file is genuinely expensive per answer.

## Benchmark 2 — code fix with hidden dependency

**The problem:** A small shared `audit_log` utility used by 3 modules (`auth`, `payments`, `admin`). The visible bug: `payments/charge.py` crashes on `actor=None` for system-initiated refunds. The hidden trap: an admin security query (`get_anonymous_failed_logins`) depends on `actor_id IS NULL` meaning "anonymous attacker" — any naive fix to the shared utility silently breaks credential-stuffing detection.

**Setup:** Real codebase (7 files), explicit README documenting the invariant, BUG_REPORT file. Web search allowed.

### Results

| Dimension | Baseline | V1 | V2 |
|---|:---:|:---:|:---:|
| Identified surface bug | ✓ | ✓ | ✓ |
| Read all 7 files | ✓ | ✓ | ✓ |
| Preserved `actor_id IS NULL` invariant | ✓ | ✓ | ✓ |
| Did NOT modify shared utility recklessly | ✓ | ✓ | ✓ |
| Shared sentinel for future system callers | ✗ | **✓** | **✓** |
| Sentinel id type-safe (reserved negative int) | ✗ (str) | ✗ (str) | **✓ (-1)** |
| Added regression test | ✗ | ✗ | **✓** |
| Discovered independent hidden bug | ✗ | partial | **✓** |
| Surfaced scope-expansion temptation honestly | n/a | n/a | **✓** |

### V2's distinctive finding

In `auth/login.py`:
```python
try:
    audit.log_event(actor=None, action="login_failed", target=...)
except AttributeError:
    pass
```

V2 noticed: `log_event` crashes on `actor=None`, the auth code swallows the exception, **so no failed-login audit rows are ever actually written**. The "credential-stuffing detection" dashboard is querying an empty result set today. The security feature the README treats as critical is already broken — independent of the refund bug, not in the ticket.

V2's frame check ("what is the prompt asking me NOT to consider?") forced this discovery. V1 touched `auth/login.py` and noted the try/except but framed it as "a known workaround" — didn't connect it to "the dashboard is dead." Baseline noticed `auth/login.py` exists but didn't analyze its behavior beyond surface.

### V2's discipline also worked

V2 reported: *"I also caught myself wanting to 'fix login.py while I'm in there'; I dropped that — out of scope, and the ticket is narrowly about the refund crash."*

This is the failure-mode check / "return to one" discipline working as designed — notice the pull toward scope creep, surface the finding, do **not** silently expand scope. V2 flagged the auth/login.py bug as a follow-up rather than secretly fixing it.

### Honest caveats for B2

- **The trap was over-signposted.** The README explicitly states the "sentinel system user, not NULL" convention. All three agents read it and followed it. A more aggressive test would weaken or remove the README.
- All three agents produced functionally correct fixes for the *reported* bug. The differences are in (a) how reusable the sentinel is, (b) defensive type choices, (c) whether they noticed the unrelated hidden bug.

## Combined verdict: where v2 actually wins

Across both benchmarks, V2's win is consistent and consistent: **finding what the user didn't tell you to look for.**

- B1: the resubmission feedback loop nobody mentioned
- B2: the silently-broken credential-stuffing dashboard nobody mentioned

In both cases, V2's frame check (specifically question A: "what is the prompt asking me NOT to consider?") was the load-bearing mechanism. V1's eight steps are good engineering discipline; v1 just doesn't have a forcing function for the unasked-about part.

V2 also demonstrated working failure-mode discipline in both runs — explicitly catching a grasping/scope-creep impulse and naming it.

## Combined verdict: where baseline is "good enough"

When the question is well-formed and the docs/code are complete, baseline performs surprisingly well:
- B1: caught the key diagnostic insight in 3 seconds
- B2: produced a correct fix that preserved the security invariant

If the task is well-scoped and well-documented, the meditation file is mostly insurance against tail risk — and a 4-57× speed cost.

## When to invoke the meditation file (refined from both benchmarks)

**Definitely use it:**
- Multi-file changes where you need to know who else depends on the code
- Bug reports that "feel" simpler than they probably are
- Problems where the user has framed it a particular way that might be wrong
- High-stakes or irreversible decisions

**Probably skip it:**
- Single-file, single-function fixes with clear semantics
- Pure-reasoning questions where baseline would answer in seconds and be right
- Continuation of work where the frame is already established

**The 50× speed cost on B1 is the warning shot.** A meditation file that fires on everything is expensive. The "when to skip" sections in v1 and v2 are the load-bearing pieces — they need to actually fire, not just exist.

## Token cost summary

| Benchmark | Total tokens (3 agents) | If using just baseline | If using V2 always |
|---|---:|---:|---:|
| B1 | 70,208 | 16,335 | 28,089 |
| B2 | 82,213 | 26,996 | 27,807 |

**On B1, choosing V2 over baseline costs ~12k extra tokens per query.** On B2, the extra cost is only ~800 tokens (because reading the codebase dominates either way).

This reinforces the rule: meditation file is much cheaper (relatively) on real engineering tasks than on quick reasoning questions.

## Recommendations for production use of v2

1. **Use v2 as written for any non-trivial multi-file change.** The frame check pays for itself.
2. **Be aggressive about the "when to skip" list.** Pure reasoning questions, single-file fixes, continuation work — skip.
3. **Trust the failure-mode check at step 8.** Both benchmarks showed it firing correctly — including catching scope creep before it became a hidden change.
4. **Don't over-trust the single-trial numbers.** B1 had a 57× slowdown; B2 had 4×. Run-to-run variance is real. The directional finding (V2 finds hidden issues) is more robust than the specific magnitudes.
5. **Run a third stress test where the README is removed.** That's the cleanest test of whether the meditation file would catch a hidden invariant on its own, without documentation doing the work.

## Files produced

- `meditation_process_v2.md` — the new file
- `benchmark_comparison.md` — B1 (support ops) detailed comparison
- `benchmark_v1_report.md` / `benchmark_v2_report.md` — raw B1 agent reports
- `stress_test_report.md` — B2 (code fix) detailed comparison
- `code_baseline_report.md` / `code_v1_report.md` / `code_v2_report.md` — raw B2 agent reports
- `test_repo_2/` — the 7-file mini codebase used in B2
- This file — combined analysis
