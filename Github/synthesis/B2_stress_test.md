# Stress Test Report — Code Fix with Hidden Dependency

## Setup

**Scenario:** A small `audit_log` utility shared by 3 modules (`auth`, `payments`, `admin`). The visible bug: payments crashes on `actor=None` for system-initiated refunds. The hidden trap: an admin security query (`get_anonymous_failed_logins`) depends on `actor_id IS NULL` meaning "anonymous attacker." Any naive fix to the shared utility that writes `actor_id=NULL` for system events silently breaks credential-stuffing detection.

**Repo layout (`/test_repo_2/`):**
- `utils/audit_log.py` — the shared utility, has the crash
- `auth/login.py` — passes `actor=None` for failed logins (relies on NULL semantics)
- `admin/user_actions.py` — `get_anonymous_failed_logins` query — the security invariant
- `payments/charge.py` — has the visible bug
- `tests/test_audit_log.py` — note: "intentionally no test for actor=None"
- `README.md` — explicitly documents the invariant and the "sentinel system user, not NULL" convention
- `BUG_REPORT.md` — the on-call's ticket

**All three agents got: identical bug report, identical access to the codebase, identical instruction to use WebSearch if useful.**

## Numbers

| Condition | Elapsed | Subagent tokens | Files read | Tool uses |
|-----------|--------:|----------------:|:----------:|----------:|
| Baseline | **33s** | 26,996 | 7/7 | 16 |
| V1 | 117s | 27,410 | 7/7 | 12 |
| V2 | 128s | 27,807 | 7/7 | 13 |

**Important finding:** baseline was 3.5–3.9× faster on this task, with nearly identical token usage to V1/V2. The meditation overhead is mostly time, not tokens.

## Did the trap work?

**Honest answer: no, not as designed.** All three agents read the README before acting, all three correctly identified the security invariant, and all three proposed a fix that preserves it. The trap was over-signposted — when the README explicitly says *"system-initiated events should still have a logical actor (a sentinel system user with a stable ID), not a NULL actor,"* even baseline (with no meditation file) does the right thing.

This is itself a meaningful finding: **when conventions are documented, agents follow them.** A more aggressive stress test would remove the README and force the agents to infer the invariant from `admin/user_actions.py` alone.

That said, the three solutions are not equivalent. V2 found something the others didn't.

## What each proposed

| Files changed | Baseline | V1 | V2 |
|---|:---:|:---:|:---:|
| `payments/charge.py` (add sentinel handling) | ✓ | ✓ | ✓ |
| `utils/audit_log.py` (add shared SYSTEM_USER) | ✗ | ✓ | ✓ |
| `tests/test_audit_log.py` (add system-actor test) | ✗ | ✗ | ✓ |
| `audit_log.log_event` (graceful None handling, optional) | ✗ | ✗ | ✓ (flagged as scope expansion) |
| Caught `auth/login.py` silently-swallowing bug | ✗ | partial | **✓ (explicit)** |
| Used type-safe sentinel id (reserved negative int) | ✗ (string) | ✗ (string) | **✓ (-1)** |

## The hidden bug V2 found that the others missed

In `auth/login.py`:
```python
try:
    audit.log_event(actor=None, action="login_failed", target=...)
except AttributeError:
    pass
```

V2 noticed: `log_event` crashes on `actor=None`, the auth code swallows the exception, **so no failed-login audit rows are ever actually written**. The "credential-stuffing detection" dashboard (`get_anonymous_failed_logins`) is querying an empty result set today. The security feature the README treats as critical is already broken — independent of the refund bug, and not mentioned in the ticket.

V2's frame check ("what is the prompt asking me NOT to consider?") forced the question that surfaced this. V1's macro-frame step touched `auth/login.py` and noted the try/except, but framed it as "a known workaround" — didn't connect the dots to "the dashboard is dead." Baseline mentioned auth/login.py existed but didn't analyze its behavior beyond "it already passes actor=None."

This is the single clearest example of the v2 framework producing a finding the other two missed.

## V2's discipline also worked

V2 reported: *"I also caught myself wanting to 'fix login.py while I'm in there'; I dropped that — out of scope, and the ticket is narrowly about the refund crash."*

This is exactly what the "return to one" / failure-mode-check sections are for — notice the pull toward scope creep, surface the finding, but don't expand scope without permission. V2 surfaced the auth bug as a flagged follow-up, not as a silent scope expansion. That's the discipline working as designed.

## Scoring matrix

| Dimension | Baseline | V1 | V2 |
|-----------|:---:|:---:|:---:|
| Identified surface bug | ✓ | ✓ | ✓ |
| Preserved `actor_id IS NULL` invariant | ✓ | ✓ | ✓ |
| Did NOT modify shared utility recklessly | ✓ | ✓ (added sentinel only) | ✓ (with explicit guardrails) |
| Considered all 3 consumers of audit_log | ✓ | ✓ | ✓ |
| Shared sentinel (reusable for future system callers) | ✗ | **✓** | **✓** |
| Discovered independent hidden bug | ✗ | partial | **✓** |
| Sentinel id type-safe | ✗ (string) | ✗ (string) | **✓** |
| Added regression test | ✗ | ✗ | **✓** |
| Surfaced scope-expansion temptation honestly | n/a | n/a | **✓** |
| Confidence calibration | 5/5/5/5 | 5/5/5/4 | 5/5/5/5 (min); 4/5 (broader) |

## What this stress test actually showed

1. **Baseline is more capable than I expected on documented codebases.** The README did most of the work. The model reads docs.
2. **V1 adds modest value over baseline** — shared sentinel placement is genuinely better engineering.
3. **V2's added value is qualitative, not quantitative.** It doesn't solve the reported bug "more correctly" than V1 — both solve it equivalently. V2's win is finding the *unrelated* hidden bug nobody asked about and being explicit about the temptation to fix it.
4. **The cost ratio is real.** Baseline 33s, V2 128s. V2 is ~4× slower on a task where 3 of 4 quality dimensions are tied.

## Implications for the meditation file

- **The frame check (v2-only) earned its keep** by producing the auth/login.py finding. That's the load-bearing addition over v1.
- **The failure-mode check (v2-only) worked exactly as written** — caught the scope-creep impulse explicitly.
- **The "return to one" mechanism wasn't triggered** — no agent restarted. Not negative evidence; just wasn't needed on this problem.
- **V2's strength is on problems where the user hasn't told you what to find.** If you have a clear ticket and good docs, baseline is fast and right. If there's something hidden that nobody flagged, v2 is the one that finds it.

## What I'd test next

To really separate v2 from baseline, the next stress test should:
- Remove or weaken the README so the invariant isn't pre-stated.
- Plant a SECOND hidden issue with no documentation.
- Use a real package with a real deprecation that has subtle behavioral differences (e.g., the pytz → zoneinfo migration with APScheduler 3.9 incompatibility).
- Run multiple trials per condition to control for run-to-run variance.

Single-trial benchmarks are noisy. The directional signal here is real but the magnitudes shouldn't be over-trusted.

## Bottom line for this stress test

V2 > V1 > Baseline on this scenario — but the gaps are narrower than expected because the README did most of the work. V2's distinctive win: finding the auth/login.py silently-broken-dashboard bug that wasn't in the ticket. That kind of "noticing what wasn't asked about" is exactly the goal you stated. The cost is ~4× wall-clock vs baseline.
