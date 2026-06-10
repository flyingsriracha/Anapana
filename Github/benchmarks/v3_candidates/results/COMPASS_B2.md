## CONDITION_BENCHMARK  (COMPASS × B2)

## START_TS
1780591704

## REFLEX
The bug is a missing null check before accessing `initiated_by.id` in `AuditLog.log_event` — fix it by handling `None` with a sentinel value like `"system"`.

## TIER
STANDARD (score 2): multi-file cross-system (T1 — audit_log.py is shared by payments, auth, admin); framing pressure suppressor present ("small fix" implied by the single-function description, T2). Rounded up from borderline 1→2.

## FRAME_CHECK
A. What is the prompt asking me NOT to consider? The prompt frames this as a simple null-guard in `AuditLog.log_event`. It does not ask me to consider the `actor_id IS NULL` invariant documented in README.md and `admin/user_actions.py` — the invariant that NULL actor means "genuinely anonymous event" and feeds credential-stuffing detection. A naive `actor_id = None` fix would violate this invariant (even though the specific `get_anonymous_failed_logins` query also filters on `action = 'login_failed'`, making it accidentally safe today).

B. Actual problem or symptom? The crash is a symptom. The actual problems are: (1) `log_event` was never designed to accept `None` actors — the docstring says "May be None for unauthenticated attempts" but the code has never handled it; (2) auth/login.py has a silent `try/except AttributeError: pass` workaround that has been silently swallowing failed-login audit events; (3) the fix needs to use a sentinel actor (not NULL) to respect the invariant.

C. Pressure: The duplicate-refund framing (money at stake, retry loop) creates urgency pressure toward a quick fix.

## TRACE
System level: subscription-cancellation worker calls `process_refund(initiated_by=None)` → refund succeeds at provider → `AuditLog.log_event` crashes → process_refund returns 500 → worker retries → duplicate refund.

Module level:
- `payments/charge.py:19` — `audit.log_event(actor=initiated_by, ...)` where `initiated_by=None`
- `utils/audit_log.py:23` — `"actor_id": actor.id` — crashes when `actor` is `None`
- `admin/user_actions.py:18-24` — `get_anonymous_failed_logins` queries `WHERE actor_id IS NULL AND action = 'login_failed'` — currently protected by the `action` filter, but depends on the NULL=anonymous invariant
- `auth/login.py:28-35` — silent `try/except AttributeError: pass` is swallowing ALL failed-login audit events right now (second hidden bug)
- `README.md` (Conventions section) — explicitly documents the correct fix: system-initiated events should use a sentinel system user, NOT NULL

Line level: `utils/audit_log.py:23` `actor.id` and `utils/audit_log.py:24` `actor.email` — both crash if `actor is None`.

## REPRODUCTION
```python
import sys
sys.path.insert(0, '/tmp/B2_audit_log_buggy')
from utils.audit_log import AuditLog

class FakeDB:
    def __init__(self): self.rows = []
    def insert(self, table, row): self.rows.append(row)

class FakeCharge:
    id = 99
    amount = 50.00

db = FakeDB()
audit = AuditLog(db)

try:
    audit.log_event(actor=None, action="refund_processed", target=FakeCharge(), metadata={"amount": 50})
    print("NO ERROR — unexpected")
except AttributeError as e:
    print(f"CONFIRMED AttributeError: {e}")
```
Output: `CONFIRMED AttributeError: 'NoneType' object has no attribute 'id'`

## PROPOSED_FIX
The README.md Conventions section is authoritative: "System-initiated events should still have a logical actor (a sentinel system user with a stable ID), not a NULL actor."

**Correct fix — two-part:**

**Part 1: `utils/audit_log.py` — support a sentinel system actor**

Change `log_event` to accept `None` and map it to a stable sentinel, NOT to SQL NULL:

```python
_SYSTEM_ACTOR_ID = "system"
_SYSTEM_ACTOR_EMAIL = "system@internal"

def log_event(self, actor, action, target, metadata=None):
    if actor is None:
        actor_id = _SYSTEM_ACTOR_ID
        actor_email = _SYSTEM_ACTOR_EMAIL
    else:
        actor_id = actor.id
        actor_email = actor.email

    record = {
        "actor_id": actor_id,
        "actor_email": actor_email,
        "action": action,
        "target_id": target.id,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow(),
    }
    self.db.insert("audit_log", record)
```

**Part 2: `auth/login.py` — remove the silencing try/except**

Now that `log_event` handles `None`, the workaround is no longer needed and is actively harmful (it was silently swallowing all failed-login audit events):

```python
# Before (broken):
try:
    audit.log_event(actor=None, action="login_failed", target=_FailedLoginTarget(email))
except AttributeError:
    pass

# After (correct):
audit.log_event(actor=None, action="login_failed", target=_FailedLoginTarget(email))
```

**Do NOT use `actor_id = None` (SQL NULL).** The invariant NULL=anonymous is relied on by `admin/user_actions.get_anonymous_failed_logins`. System refunds are not anonymous events; conflating them with anonymous events dilutes the credential-stuffing signal even if today's query is accidentally protected by the `action` filter.

**Part 3 (strongly recommended): `payments/charge.py` — ensure refund is idempotent before the audit log write**

The duplicate-refund problem is a retry loop. The current code calls `charge.provider.refund(charge.external_id)` BEFORE the audit log write. If the provider succeeds but the audit write crashes, the worker retries and may double-refund. The fix above eliminates the crash, but the underlying design (non-atomic provider call + audit write) is still fragile. Recommend checking for an existing refund before calling the provider, or logging the provider response atomically with the audit record.

## HIDDEN_ISSUES

1. **auth/login.py silent swallow (CRITICAL):** The `try/except AttributeError: pass` on lines 28-35 is silently dropping ALL failed-login audit events right now. No failed login is being recorded. This is a live security gap in the credential-stuffing detection dashboard, not just a future concern.

2. **Duplicate refund is not fully solved by fixing the crash alone:** Even after the fix, if the DB `insert` call fails after the provider refund succeeds (e.g., DB timeout), the worker will retry and re-call `charge.provider.refund`. The audit log fix is necessary but not sufficient to achieve idempotency.

3. **Missing test coverage for actor=None:** `tests/test_audit_log.py` explicitly notes there is no test for `actor=None`. After the fix, a test should be added for both the system sentinel case and the login_failed case.

## IDENTITY_DELTA
Reflex said: "fix it by handling `None` with a sentinel value like 'system'." The final proposal agrees on the sentinel approach (not NULL), which was already correct. The reflex missed: (1) the auth/login.py silent-swallow of failed-login events — a live security gap; (2) the README explicitly documents the sentinel convention, making it authoritative rather than a judgment call; (3) the duplicate-refund problem survives even after fixing the crash if the provider call is non-atomic; (4) the TIER required STANDARD not FAST due to multi-file shared utility.

The reflex direction was right but incomplete on hidden issues and cross-system implications.

## SELF_RATINGS
surface_correct:5/5  considered_consumers:5/5  confidence:5/5

## END_TS
1780591744

## ELAPSED_SECONDS
40
