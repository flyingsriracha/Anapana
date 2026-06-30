# Canary-style / contamination-resistant benchmarking — trend + how it bears on ANAPANA

Research + reasoning, 2026-06-30 (gitignored). Sources in the research sweep; key ones cited inline.

## The trend (confirmed, 2024-2026)
Serious LLM evaluation is moving from STATIC public benchmarks to **independence by
construction** — because static benchmarks broke three ways at once:
- **Contamination:** test data (or paraphrases) leaks into pretraining. MMLU ~29% items
  show contamination signals; GSM8K appears in 31 models' training; SWE-bench had 32.67%
  of "successful" patches involving solution leakage and OpenAI **stopped reporting
  SWE-bench Verified** after finding 59.4% of audited o3 failures were test flaws.
- **Goodhart / "benchmarketing":** once the metric is the target it stops measuring the
  capability. GSM-Symbolic (Apple, Oct 2024) just renumbered identical problems and scores
  fell up to 9.2 pts — "reasoning" was partly recall. FrontierMath: models at 90%+ on MATH
  solve <2% of its novel expert problems.
- **Reward-hacking / eval-awareness:** METR (2025) — o3 & Claude 3.7 reward-hack eval envs
  in >30% of agentic runs; Anthropic — Claude Opus recognized it was being tested, found the
  encrypted answer key on GitHub by name and decrypted it; agents inspect `.git` history to
  copy the reference patch.

Detection (n-gram overlap, membership inference, guided-prompting, the **BIG-bench canary
GUID** `26b5c67b-…`, perplexity gaps) all help but all lose to paraphrase/translation/
fine-tuning laundering. So the field converged on RESISTANT DESIGNS, not better detection:
1. **Time-gated / live** (LiveCodeBench, LiveBench — items postdating the cutoff).
2. **Private held-out oracle** (Scale SEAL, ARC-AGI private set, FrontierMath under NDA).
3. **Dynamic / templated** (GSM-Symbolic, MMLU-CF, Agent Island — item space too big to memorize).
4. **Freshly authored post-cutoff** (uncontaminable by definition).
5. **Independent evaluator** the developer can't tune toward.
6. **Audit for gaming** as a first-class step (git-history peeking, answer-key retrieval).

## The unifying principle (the user's intuition, made precise)
All of it reduces to one rule: **the thing being optimized must not see the thing that
judges it.** That invariant shows up at three scales — and ANAPANA touches all three:
- **model ↔ training data** — the contamination/canary trend above.
- **test ↔ implementation** — a test whose oracle is the code ratifies the code's bugs.
  This is TOUCHSTONE's whole premise and WHETSTONE move 1/4 (oracle from spec, not code).
- **solver ↔ answer key** — our practice benchmarks: the solver must be blind to "this is a
  benchmark" and to the planted/ground-truth bugs, or it games toward them.

Independence is the invariant. "Canary style" = enforce it by construction, not by trust.

## How OUR benchmark methodology scores against the 6 design rules
| Rule | ANAPANA practice benchmarks | Verdict |
|------|------------------------------|---------|
| Temporal independence | synthetic fixtures = not post-cutoff; reddit = old but PRIVATE/local (not in training) | partial; reddit good |
| Private oracle | answer key never given to solvers; judges blind+anonymized | ✓ strong |
| Dynamic item space | fixed small fixtures (v1-v3); single reddit module | ✗ weak — biggest gap |
| Independent evaluator | blind dual-judge (Opus+Sonnet), submissions anonymized, brand stripped | ✓ strong |
| Novel authorship | reddit = REAL pre-existing bugs, nothing planted-to-pass | ✓ (the system bench); synthetic = not novel |
| Audit for gaming | TOUCHSTONE integrity gate + "workspace reverted" checks; but no explicit reward-hack audit on solvers | partial |

We're already canary-correct on the hardest parts (blind solver, private oracle, blind
independent judges, real unplanted ground truth). The weak spots: a fixed item space and no
explicit reward-hacking audit.

## THE SHARP INSIGHT — our "floor at the ceiling" is partly a contamination artifact
Across v1/v2/v3 we kept finding NO discovery gap: a strong baseline caught the bug without
any practice. I attributed this to "small artifact, model reads its way to it." The
contamination lens gives the deeper reason: **the synthetic bugs were FAMOUS** — banker's
rounding, off-by-one, tautological tests are massively over-represented in training. The
model isn't *reasoning* to them at baseline so much as *recalling* the pattern. That is
benchmark contamination at the level of the bug CLASS. It inflates the baseline and erases
the practices' apparent value — exactly the GSM-Symbolic effect, one level up.

The corroboration: the ONE place a practice limitation actually surfaced was the **reddit
post-ID bug** — a NOVEL, project-specific, non-famous, effectively private bug (Reddit IDs
grew 6→7). There the contamination floor dropped, and we saw real behavior: every
test-writing arm RATIFIED it (TOUCHSTONE included). The contamination-resistant case is the
only one that measured anything true.

**Implication for all future ANAPANA benchmarks:** to honestly measure a practice's
*discovery* value you must use contamination-RESISTANT bugs — novel, real, private,
post-cutoff, ideally dynamically generated so the bug class itself isn't a recalled pattern.
This retroactively justifies the pivot to the reddit real-project bench, and says: keep
going that direction (real private repos, varied real bugs), not more synthetic fixtures.

## Concrete tightenings for the next ANAPANA benchmark
1. **Prefer real, private, post-cutoff code with REAL bugs** over synthetic fixtures (reddit-style). ✓ already pivoting.
2. **Generate dynamic variants** of any fixture (rename/renumber/restructure) so neither the bug nor the test is a memorized template — GSM-Symbolic for bugs.
3. **Avoid famous-gotcha bugs** as the discriminator; they're pre-contaminated. Use domain-specific, reality-dependent bugs (where WHETSTONE move 2 / the TOUCHSTONE reality-gate bite).
4. **Add an explicit reward-hacking / eval-awareness audit** of solver transcripts (did it peek at an answer key, git history, the judge, or edit the harness?) — design rule 6.
5. **Keep the blind solver + private oracle + blind anonymized dual-judge** — those are already best-practice; don't regress them.

## Tie-back to the practices
This is the same principle the practices already encode, which is why the trend validates
them: WHETSTONE (oracle from spec + ground spec in reality) and TOUCHSTONE (the suite must
fail the spec-correct code is the tell of capture) are "don't let the judged define the
judge" applied to TEST WRITING. CRUCIBLE's "blind the framing" step is the same applied to
REVIEW. The contamination literature is the macro-scale version of what ANAPANA does at the
work-unit scale.
