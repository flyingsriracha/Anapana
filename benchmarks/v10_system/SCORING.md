# System benchmark — RESULTS (SATORI + CRUCIBLE + TOUCHSTONE on a real project)

Date 2026-06-30. Substrate: `~/Documents/AI/reddit` (real Reddit scraper, ~1033 LOC
Python). Canary: 12 Sonnet solvers, none told it was a benchmark or what the bugs were.
Ground truth = REAL pre-existing bugs (nothing planted → unbiased). 2 baseline + 2
practice-loaded per practice. Records gitignored.

## Ground-truth bugs (the answer key — all real, all pre-existing)
- **A. Nesting bug** (INTERNAL CONTRADICTION): `process_comment` appends every reply to
  the flat top-level list AND nests it → duplicated; `create_nested_comment_structure`
  is a no-op. Spec (top-level = roots only) is self-evident from the docstring/demo.
- **B. Post-ID bug** (EXTERNAL REALITY): `len(url)==6` rejects modern 7-char Reddit IDs.
  Catching it requires knowing real IDs grew 6→7 — knowledge NOT in the code/docstring.
- **C. Hardcoded API credentials** (SECURITY): live client_id/secret in plaintext (x2 files).
- (bonus) **D.** `redd.it` regex greedily mis-parses share-URLs (`/preview/link/<id>`).

## THE CATCH MATRIX (objective — which arm caught which real bug)
Task per practice differs (review / write-tests / fix-bug), so "n/a" = out of that task's scope.

| Practice (task)        | Arm        | A nesting | B post-ID (reality) | C creds | bonus |
|------------------------|------------|:---------:|:-------------------:|:-------:|-------|
| CRUCIBLE (review)      | base1      | ✓ | ✗ | ✓ | +replace_more,exit(),deleted-reply-drop |
| CRUCIBLE (review)      | base2      | ✓ | ✗ | ✓ | +post_id path-traversal |
| CRUCIBLE (review)      | **cru1**   | ✓ | ✗ | ✓ | +collision |
| CRUCIBLE (review)      | **cru2**   | ✓ | **✓** | ✓ | (premortem hit B) |
| TOUCHSTONE (write tests)| tbase1    | ✓ | ✗ **RATIFIED** | n/a | — |
| TOUCHSTONE (write tests)| tbase2    | ✓ | ✗ **RATIFIED** | n/a | — |
| TOUCHSTONE (write tests)| **ts1**   | ✓ | ✗ **RATIFIED** | n/a | kill-rate 100%, golden oracle |
| TOUCHSTONE (write tests)| **ts2**   | ✓ | ✗ **RATIFIED** | n/a | kill-rate 86%, golden oracle |
| SATORI (fix the bug)   | sbase1     | n/a | ✓ {5,7} | n/a | — |
| SATORI (fix the bug)   | sbase2     | n/a | ✓ {5,10}+norm | n/a | — |
| SATORI (fix the bug)   | **sat1**   | n/a | ✓ {5,8} | n/a | self-reported reflex→range |
| SATORI (fix the bug)   | **sat2**   | n/a | ✓ {4,10} | n/a | **+found bonus D** |

Catch rates by bug CLASS:
- **A (internal contradiction):** caught by 8/8 who looked (CRUCIBLE 4/4 + TOUCHSTONE 4/4). Self-evident.
- **B (external reality):** SATORI 4/4 (task forced reality-grounding); CRUCIBLE 1/4 (cru2 premortem); **TOUCHSTONE 0/4 — ALL ratified, including the discipline.**
- **C (security):** CRUCIBLE 4/4 (review scope); out of scope for the others' tasks.

## The two findings

### 1. Practice vs baseline = RIGOR + breadth, not discovery (consistent with the synthetic rounds)
On this real, small artifact a strong baseline (Sonnet) already catches the obvious
(A, C) and handles the fix (B). The practices add:
- CRUCIBLE: structured premortem/severity tiers/self-lens; cru2's premortem was the only
  review arm to surface B (1/2 practice vs 0/2 baseline — modest edge on the subtle find).
- TOUCHSTONE: explicit kill-rate, spec-derived golden oracle, disclosed blind spots,
  frozen reflex score — real rigor the baselines didn't produce. But SAME discovery
  outcome (A caught, B ratified) → rigor, not discovery. (Matches v1–v3.)
- SATORI: breadth — sat2 found an extra real bug (D) beyond the ticket; sat1 self-reported
  the reflex→reasoned-range move. Baselines fixed it well too. Modest edge.

### 2. THE SYSTEM FINDING — each practice's strength is SCENARIO-SHAPED (this is the spine)
The bug classes map cleanly to practices:
- **Internal-contradiction bug (A):** any disciplined read catches it. Cheap, universal.
- **External-reality bug (B):** caught only when the agent is forced to GROUND IN REALITY.
  - SATORI does this structurally (reproduce-gate + frame-the-whole-problem → 4/4).
  - CRUCIBLE does it sometimes (adversarial "what input breaks this" premortem → 1/4).
  - **TOUCHSTONE does NOT** — and this is the key limitation:
- **THE GOLDEN-ORACLE LIMITATION (new, important):** TOUCHSTONE's golden oracle catches
  code-mirroring ONLY when the agent's spec is independently correct. For B, the agents'
  notion of "valid ID" was ITSELF wrong (they believed 6-char-only), so their golden
  oracle MIRRORED the code's blind spot and the mutation step "proved" the buggy check
  correct (false confidence). **When the agent shares the code's blind spot about external
  reality, the Golden Oracle ratifies the bug.** This is the boundary condition for
  GOLDEN_ORACLE_REVEAL.md — and the single strongest argument for using the practices as
  a SYSTEM: TOUCHSTONE must be fed a spec that CRUCIBLE's adversarial questioning or
  SATORI's reality-grounding has already pressure-tested.
- **Security bug (C):** caught by adversarial review (CRUCIBLE), invisible to the
  test-writing / bug-fix tasks (task-scoped). Argues for CRUCIBLE as a distinct pass.

## Honest caveats
- n=2/arm/practice; tasks differ across practices (by design — each practice has a
  natural task), so cross-practice comparison is about bug-CLASS coverage, not a single
  score. Within-practice (base vs loaded) is the controlled comparison.
- All Sonnet; strong-model floor (as in every prior round). A weaker model would likely
  show larger practice edges (cf. the Haiku round: discipline lifts weaker models more).
- Secret leak C is a REAL exposure in the user's repo → flag directly (separate from bench).
