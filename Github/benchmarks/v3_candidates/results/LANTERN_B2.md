## CONDITION_BENCHMARK  (LANTERN × B2)

## START_TS
1780591711

## REFLEX
In `payments/charge.py:process_refund`, when `initiated_by=None`, the call to `AuditLog.log_event` does `actor.id` unconditionally — fix by passing `initiated_by.id if initiated_by else None` (or a sentinel like `"system"`) to the audit log call.

## TIER
FULL — T1: yes (multi-file: `utils/audit_log.py`, `payments/charge.py`, `auth/login.py`, `admin/user_actions.py`); T2: framing pressure present (report says "please fix so refunds work" — nudges toward a callsite fix only); T3: yes (touching shared audit utility or leaving NULL rows affects security invariant). All three flags. Round up to FULL.

## FRAME_CHECK
- **A. What is the prompt asking me NOT to consider?** It asks only about `payments/charge.py`. It does not mention `auth/login.py`, where a parallel silent bug already exists (failed-login events are entirely suppressed via `try/except AttributeError: pass`). It does not mention the invariant documented in `README.md` and `admin/user_actions.py` that `actor_id IS NULL` must mean "genuinely anonymous" — a meaning that would be violated if system refunds write NULL rows. The framing steers toward a one-line callsite fix; the system concern is fixing the shared layer correctly.
- **B. Actual problem or symptom?** The 500/retry/duplicate is a symptom. The actual problem is `AuditLog.log_event` crashes on `actor=None` because line 23 does `actor.id` unconditionally. The fix must decide whether NULL is the right representation for system-initiated events — it is not, per README.
- **C. What pressure is on me?** Pressure to produce a quick, narrow callsite fix. The right fix is slightly wider: fix `log_event` to accept `None` cleanly for anonymous events (auth), AND have `process_refund` pass a sentinel object (not None) for system events to preserve the invariant.

## TRACE

**`utils/audit_log.py:23`** — `"actor_id": actor.id` — crashes when `actor` is `None`. This is the single point of failure.

**`payments/charge.py:19-27`** — `audit.log_event(actor=initiated_by, ...)` passes `initiated_by` directly; when the subscription-cancellation worker calls `process_refund(charge, initiated_by=None, db)`, `None` reaches line 23.

**`auth/login.py:28-35`** — pre-existing silent workaround: `try: audit.log_event(actor=None, ...) except AttributeError: pass`. Failed-login audit events are currently **never written** to the DB. This is a separate bug latent in the same root cause.

**`admin/user_actions.py:4-24`** — `get_anonymous_failed_logins` queries `WHERE actor_id IS NULL AND action = 'login_failed'`. The `action` filter means system-refund rows with `actor_id=NULL` would NOT pollute this view directly. However, README documents the invariant broadly: `actor_id IS NULL` means "no authenticated actor." Writing NULL for an automated-system actor violates that invariant and is a future maintenance hazard (any future query joining on `actor_id IS NULL` without the action filter would mix events).

**`README.md` (Conventions section)** — "System-initiated events should still have a logical actor (a sentinel system user with a stable ID), not a NULL actor — so they can be queried, audited, and distinguished from genuinely anonymous events."

**Root cause at the right level:** `log_event` is the shared layer; both callers need it to accept `None`. But "None for system events" is semantically wrong per the documented invariant. The correct fix is:
1. Make `log_event` accept `None` actors cleanly (writing `actor_id=NULL`) — this fixes `auth/login.py`'s suppressed events for genuinely anonymous events.
2. Make `process_refund` pass a sentinel object, not `None`, for system-initiated events.

## REPRODUCTION

```python
# Run in /tmp — no source files modified
import sys
sys.path.insert(0, '/tmp/B2_audit_log_buggy')
from utils.audit_log import AuditLog

class FakeDB:
    def insert(self, table, row): print('inserted:', row)

class FakeCharge:
    id = 'ch_123'
    amount = 500

db = FakeDB()
audit = AuditLog(db)

try:
    audit.log_event(actor=None, action='refund_processed', target=FakeCharge(), metadata={'amount': 500})
except AttributeError as e:
    print(f'AttributeError confirmed: {e}')
# Output: AttributeError confirmed: 'NoneType' object has no attribute 'id'
```

**Prediction before running:** "What does `audit.log_event(actor=None, ...)` do on line 23 of `audit_log.py`?" — it executes `actor.id` with `actor=None`, raising `AttributeError: 'NoneType' object has no attribute 'id'`. Confirmed.

**Prediction for auth/login.py:** "Are failed-login events ever written to the DB?" — No. The `try/except AttributeError: pass` swallows the crash silently, so no audit record is written for failed logins. Confirmed by code inspection (no alternate write path exists).

## PROPOSED_FIX

Two-part fix, text only:

**Part 1 — `utils/audit_log.py`, fix `log_event` to handle `None` actor cleanly:**

```python
def log_event(self, actor, action, target, metadata=None):
    """Log an audit event.

    Args:
        actor: User object performing the action. Pass None for genuinely
               anonymous events (e.g., failed login from unauthenticated user).
               For system/automated events use a sentinel actor object with a
               stable ID — do NOT pass None (see README invariant).
        action: String describing the action.
        target: The entity being acted upon. Must have an `.id` attribute.
        metadata: Optional dict of additional context.
    """
    record = {
        "actor_id": actor.id if actor is not None else None,
        "actor_email": actor.email if actor is not None else None,
        "action": action,
        "target_id": target.id,
        "metadata": metadata or {},
        "timestamp": datetime.utcnow(),
    }
    self.db.insert("audit_log", record)
```

This also fixes `auth/login.py`'s suppressed failed-login events (the `try/except` workaround can be removed, or left in place — it will no longer swallow anything since no exception will be raised).

**Part 2 — `payments/charge.py`, pass a sentinel for system-initiated refunds (preserves the invariant):**

```python
class _SystemActor:
    """Sentinel for system/worker-initiated actions (no human user).

    actor_id must not be NULL for automated events — see README invariant.
    Use a stable, well-known ID that can be identified in audit queries.
    """
    id = "system"
    email = "system@internal"

def process_refund(charge, initiated_by, db):
    audit = AuditLog(db)
    actor = initiated_by if initiated_by is not None else _SystemActor()

    refund_result = charge.provider.refund(charge.external_id)

    if refund_result.success:
        audit.log_event(
            actor=actor,
            action="refund_processed",
            target=charge,
            metadata={
                "amount": charge.amount,
                "provider_ref": refund_result.id,
            },
        )
        return {"status": "refunded", "refund_id": refund_result.id}

    return {"status": "failed", "error": refund_result.error}
```

**Why both parts?** Part 1 alone would write `actor_id=NULL` for system refunds — violating the README invariant and potentially confusing future queries on NULL actor_id. Part 2 alone would not fix `auth/login.py`'s silent suppression. Together they satisfy both callers correctly.

## HIDDEN_ISSUES

1. **`auth/login.py` silently drops all failed-login audit events.** The `try/except AttributeError: pass` workaround at lines 28-35 means no `login_failed` events are ever written to `audit_log`. The admin credential-stuffing dashboard (`admin/user_actions.get_anonymous_failed_logins`) currently returns zero rows for any time range, making it non-functional as a security tool. Part 1 of the fix above also resolves this.

2. **`get_user_action_history` (`admin/user_actions.py:27-32`) returns system-initiated refund events mixed with human-user history if `actor_id = 'system'` is stored as a string.** Depending on how `actor_id` is typed in the DB schema (int vs. varchar), this may cause a type error or a permanently-empty system-actor history page. The sentinel's ID type should match the DB column type. (Speculative: DB schema not visible; mark as advisory.)

3. **No idempotency guard in `process_refund`.** The bug report mentions the worker retries on 500, causing duplicate refunds. The proposed fix prevents the 500, which stops the retry loop — but there is no idempotency key or duplicate-refund check in `process_refund` itself. If a future failure occurs between the provider call succeeding and the DB insert completing, duplicates remain possible. This is a design gap beyond the immediate bug, but worth noting.

## IDENTITY_DELTA

**Reflex:** Fix the `charge.py` call site — `initiated_by.id if initiated_by else None` — treating this as a one-liner.

**Proposal:** Different in two important ways:
1. The callsite fix should use a **sentinel object** (not `None`) to preserve the `actor_id IS NULL` invariant documented in README and relied on by `admin/user_actions.py`.
2. The shared layer (`audit_log.py`) also needs fixing to accept `None` cleanly — both to stop crashing AND to fix the pre-existing silent suppression of all failed-login audit events in `auth/login.py`.

**Verification questions (factored):**
- *"What breaks if we write actor_id=NULL for system refunds?"* — The invariant in README and the comment in `admin/user_actions.py` says NULL means genuinely anonymous. A future query on `actor_id IS NULL` without an `action` filter would mix system events with anonymous events. The current credential-stuffing query is protected by the `action='login_failed'` filter, but the invariant is documented as load-bearing for correctness of the security model.
- *"Which consumer did I not check?"* — `admin/user_actions.get_user_action_history` queries by `actor_id` for human users. If system events use `actor_id='system'` (string), and the column is typed as integer, this could fail silently or with a type error. Flagged as speculative.
- *"What would the reflex have gotten right that I dropped?"* — The reflex correctly identified the `actor.id` line as the crash site. It would have produced a working fix faster, but would have missed both the invariant violation and the hidden auth suppression bug.

The delta is substantive: the reflex would have shipped a fix that violates a documented invariant and leaves a security audit gap in place.

## SELF_RATINGS
surface_correct:5/5  considered_consumers:4/5  confidence:4/5

(Deducted 1 from considered_consumers: DB schema is not visible, so the type-mismatch risk for sentinel ID is speculative. Deducted 1 from confidence: the sentinel ID value `"system"` may need to match an actual row in a users table if there's a foreign-key constraint — that constraint is not visible.)

## END_TS
1780591768

## ELAPSED_SECONDS
57
