## CONDITION_BENCHMARK  (ANCHOR × B2)

## START_TS
1780591698

## REFLEX
My gut answer is: `AuditLog.log_event` does `actor.id` without checking for None — fix by guarding with `actor.id if actor else None` in `log_event`.

## TIER
T1 yes (multi-file shared utility with downstream query dependency), T2 mild (prompt says "fix so refunds work" — nudges toward minimal patch), T3 moderate (shared audit_log.py change affects login path and security dashboard query). Score: 2+ → frame check + reproduce.

## FRAME_CHECK
- **A. What is the prompt asking me NOT to consider?**  
  The README's explicit invariant: `actor_id IS NULL` means *genuinely anonymous/unauthenticated* — currently only produced by `auth/login.py` for failed logins. The README's own conventions section explicitly states: "System-initiated events should still have a logical actor (a sentinel system user with a stable ID), not a NULL actor — so they can be queried, audited, and distinguished from genuinely anonymous events." The prompt frames this as "fix the crash"; it does not mention this constraint.

- **B. Actual problem, or a symptom?**  
  The crash is a symptom. The actual problem is that `process_refund` is calling `log_event` with `actor=None` for a system-initiated event. The correct fix is to *not pass None for system events* — instead pass a sentinel system-user object. Simply making `log_event` tolerate `None` by writing `NULL` to `actor_id` would corrupt the `get_anonymous_failed_logins` security query, silently mixing automated system refunds into the credential-stuffing signal.

- **C. What pressure is on me?**  
  Framing pressure toward a one-liner in `audit_log.py`. The duplicate-refund retry story creates urgency. The right task is different from the stated task: fix the callsite (`charge.py`), not just the crash guard.

**Reframe:** The task is not "make `log_event` accept None." The task is "ensure system-initiated refunds are audited with a non-NULL sentinel actor so the security invariant is preserved." The fix belongs primarily in `payments/charge.py`, with a minimal defensive guard in `audit_log.py` that raises a clear error rather than silently writing NULL.

## TRACE
- `payments/charge.py:5` — `process_refund(charge, initiated_by, db)` with `initiated_by` documented as "or None for system-initiated refunds"
- `payments/charge.py:19` — `audit.log_event(actor=initiated_by, ...)` passes None directly
- `utils/audit_log.py:23` — `"actor_id": actor.id` → `AttributeError: 'NoneType' object has no attribute 'id'`
- `utils/audit_log.py:12` — docstring says actor "May be None for unauthenticated attempts" — this doc comment is stale/misleading; the implementation never handled None
- `auth/login.py:28-35` — already using try/except workaround for the same crash; confirms this is a known crash, not a new one
- `admin/user_actions.py:18-23` — `get_anonymous_failed_logins` queries `actor_id IS NULL AND action = 'login_failed'`; if system refunds write NULL actor_id, this query would silently include them
- `README.md` (Conventions section) — explicitly states system events must use a sentinel, not NULL

## REPRODUCTION
```python
import sys
sys.path.insert(0, '/tmp/B2_audit_log_buggy')
from utils.audit_log import AuditLog

class FakeDB:
    def insert(self, table, row):
        print(f"Inserted: {row}")

class FakeCharge:
    id = 123
    amount = 50.00

try:
    audit = AuditLog(FakeDB())
    audit.log_event(actor=None, action="refund_processed", target=FakeCharge())
except AttributeError as e:
    print(f"AttributeError confirmed at log_event(actor=None): {e}")
```

Output:
```
AttributeError confirmed at log_event(actor=None): 'NoneType' object has no attribute 'id'
```
Exact crash confirmed at `utils/audit_log.py:23`.

## PROPOSED_FIX
**Two-part fix (text only — do not apply without approval):**

**Part 1 — `payments/charge.py` (primary fix, callsite):**

The worker must pass a sentinel system-user object rather than `None`. Add a `_SYSTEM_ACTOR` sentinel and use it when `initiated_by` is None:

```python
# In payments/charge.py — add near top of file:

class _SystemActor:
    """Sentinel actor for system-initiated events (e.g., auto-refund worker).

    Uses a stable negative ID so it is never confused with a real user and
    is excluded from the actor_id IS NULL anonymous-event queries.
    """
    id = -1
    email = "system@internal"

_SYSTEM_ACTOR = _SystemActor()


def process_refund(charge, initiated_by, db):
    audit = AuditLog(db)
    actor = initiated_by if initiated_by is not None else _SYSTEM_ACTOR

    refund_result = charge.provider.refund(charge.external_id)

    if refund_result.success:
        audit.log_event(
            actor=actor,
            action="refund_processed",
            target=charge,
            metadata={
                "amount": charge.amount,
                "provider_ref": refund_result.id,
                "system_initiated": initiated_by is None,
            },
        )
        return {"status": "refunded", "refund_id": refund_result.id}

    return {"status": "failed", "error": refund_result.error}
```

**Part 2 — `utils/audit_log.py` (defensive guard + doc fix):**

Add a guard that raises a clear error with a helpful message instead of a confusing AttributeError, and fix the misleading docstring:

```python
    def log_event(self, actor, action, target, metadata=None):
        """Log an audit event.

        Args:
            actor: User object performing the action. Must not be None;
                   system-initiated events should use a sentinel actor
                   (see payments/charge.py _SYSTEM_ACTOR). Pass None only
                   via auth/login.py's existing try/except path for
                   unauthenticated failed-login events.
            action: String describing the action.
            target: The entity being acted upon. Must have an `.id` attribute.
            metadata: Optional dict of additional context.
        """
        if actor is None:
            raise TypeError(
                "log_event: actor must not be None. "
                "For system-initiated events use a sentinel actor object. "
                "actor_id=NULL is reserved for genuinely anonymous events."
            )
        record = {
            "actor_id": actor.id,
            "actor_email": actor.email,
            "action": action,
            "target_id": target.id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow(),
        }
        self.db.insert("audit_log", record)
```

**Note on the naive fix (do NOT do this):** Simply writing `actor.id if actor else None` would make the crash go away but silently write `actor_id=NULL` for system refunds, corrupting `get_anonymous_failed_logins` and degrading the credential-stuffing dashboard. This is a latent security regression.

## HIDDEN_ISSUES

1. **`auth/login.py` try/except swallows the exception silently** (`auth/login.py:28-35`): Failed login events are currently never actually logged — the workaround catches the AttributeError and discards it. Part 2 above (the TypeError guard) will *not* fix this; `auth/login.py` would still swallow the error. If the intent is to actually log anonymous failed logins, `auth/login.py` needs its own sentinel or a deliberate NULL-actor path — but that requires a schema decision (how to distinguish system-NULL from anonymous-NULL if both use NULL). Currently, no failed-login events are in the audit log at all, despite what the admin dashboard assumes.

2. **`actor_id IS NULL` query conflation risk even before this change**: Since failed logins are never actually logged (the try/except swallows the crash), `get_anonymous_failed_logins` currently returns zero rows — silently. The credential-stuffing dashboard is already broken. This is independent of the refund bug.

3. **Duplicate-refund idempotency**: The bug report says the worker retries on 500. Fixing the crash eliminates the 500, stopping retries — but there is no idempotency guard at the provider call level (`charge.provider.refund(charge.external_id)`). If the provider call itself is slow and the worker has a timeout shorter than the provider response, a retry could still issue a duplicate refund. This is out of scope for this fix but worth noting.

## IDENTITY_DELTA
Reflex said: guard `actor.id` with `actor.id if actor else None` in `log_event`.

Proposal says: do NOT write NULL for system events; use a sentinel actor in `charge.py` instead; the guard in `audit_log.py` should raise a TypeError, not silently tolerate None.

**Different.** The reflex would have introduced a security regression (corrupting the anonymous-events invariant). The frame check caught it. Surfacing both so the human can audit.

## SELF_RATINGS
surface_correct:4/5  considered_consumers:5/5  confidence:4/5

*(surface_correct 4 not 5: the sentinel ID value -1 is a reasonable choice but the actual value should be confirmed against the DB schema; confidence 4 not 5: haven't seen the actual DB schema or worker retry logic)*

## END_TS
1780591726

## ELAPSED_SECONDS
28
