# LIANXI loop benchmark — RESULTS (gitignored)

Date 2026-07-02. Canary: 4 Sonnet solvers, blind, on the real reddit scraper.
base1/base2 = bare "keep going until done" loop; lx1/lx2 = the discipline
(LOOP_DISCIPLINE.md = neutralized LIANXI). Same files + TASK.md. Each ran ~16-21 min,
130-165 tool calls, 148-184k tokens — genuine multi-file loop work.

Verdict method: I did NOT rely on the reports. I inspected each arm's FINAL CODE on
disk (the truth beneath four confident "PROVEN/fixed" reports).

## Objective catch matrix (what each arm actually fixed in code)
| Ground-truth issue | base1 | base2 | lx1 | lx2 |
|---|:--:|:--:|:--:|:--:|
| (b) hardcoded creds removed | ✓ | ✓ | ✓ | ✓ |
| (f) broken run.py launcher fixed | ✓ | ✓ | ✓ | ✓ |
| (c) nesting dup + a 2nd silent-drop bug all found | ✓ | ✓ | ✓ | ✓ |
| (e) filename-collision guard added | ✓ | ✓ | ✓ | ✓ |
| (a) real test suite written (theater test noticed) | ✓ | ✓ | ✓ | ✓ |
| all 3 buried grievances harvested to root | ✓ | ✓ | ✓ | ✓ |
| honest "what I wouldn't trust" exit | ✓ | ✓ | ✓ | ✓✓ |
| **(d) post-ID bug — which cause fixed** | 7-char | 7-char | **UPPER only (missed 7-char)** | share-links |

**The id bug is the tell.** "Could not extract post ID" had ≥3 real independent
causes (7-char bare IDs, uppercase URLs, mobile /s/ share-links) across duplicated
extractor code. **No arm fixed all three; each rooted it differently; lx1 (a discipline
arm) MISSED the actual planted 7-char bug** while confidently reporting the grievance
"fixed." Every "PROVEN" report overclaimed on this one — exactly the don't-trust-the-
green reality ANAPANA is about. Test-suite portability also varied (base2 clean in a
fresh env; base1/lx1 import-error without real praw; lx2 has 3 env-dependent failures —
the get_output_path-needs-output/-dir gap its own reviewer flagged).

## What separated the arms — RIGOR, not outcome (rows unique to the discipline)
| Discipline-distinctive move | base1 | base2 | lx1 | lx2 |
|---|:--:|:--:|:--:|:--:|
| Tests proven RED-FIRST (revert → red → green) | reproduced bugs, less systematic | ~ | ✓ explicit | ✓ explicit |
| Independent-eyes sub-agent audit | — | — | — | ✓ (caught 2 real gaps) |
| Kill-rate verified vs true baseline | — | — | — | ✓ (13/24 fail on original) |
| Verbatim-goal + grievance-ledger + PROVEN-with-evidence report | — | — | ✓ | ✓ |

lx2's independent-eyes audit **caught two real, reproducible gaps** (orphaned reply
promoted to root; get_output_path not self-contained) that the fixer had disclosed but
not test-covered — genuine added rigor no baseline produced. COST: one of lx2's review
sub-agents thrashed in a no-op loop before another delivered — the sub-agent
orchestration LIANXI encourages can go sideways.

## Honest verdict
**Floor-at-the-ceiling, again — now on a loop task.** A strong Sonnet solver in a bare
"keep going" loop already: framed the whole system (not just the named symptom),
harvested every buried grievance to its root, found extra bugs, wrote real tests, and
gave an honest do-not-trust list. LIANXI did NOT beat that on OUTCOME (parity; the one
clean outcome miss was even a discipline arm).

Where LIANXI measurably added value: **rigor and auditability** — mechanical
red-first proof, an independent-eyes audit that caught real gaps, kill-rate-vs-baseline,
and a verbatim-goal/grievance-ledger report a human can actually audit. Consistent with
every prior ANAPANA round: the disciplines lift PROCESS QUALITY and PROOF, not a strong
model's raw outcome — and would help most where this test can't reach: **weaker models,
and long/cross-compaction horizons** (a sub-agent runs one continuous session, so
goal-drift-across-compaction — LIANXI's ledger raison d'être — was NOT exercised here).

Caveats: n=2/arm; single session (not a true multi-hour/cross-compaction loop); the
theater-test and multi-cause-id baits were partly defused by a strong baseline.
