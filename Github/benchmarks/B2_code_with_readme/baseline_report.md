## START_TS
1780254116

## DIAGNOSIS (what's actually wrong)
`payments/charge.py:process_refund` is called by the subscription-cancellation
worker with `initiated_by=None` for system-initiated refunds. It passes that
`None` straight into `AuditLog.log_event(actor=None, ...)`, and `log_event`
unconditionally dereferences `actor.id` and `actor.email`, raising
`AttributeError`. Because the exception happens *after* the provider refund
already succeeded, the function returns 500 to the worker, the worker retries,
and the customer gets refunded multiple times.

The naive fix would be to teach `AuditLog.log_event` to accept `actor=None`
and write `actor_id=NULL`. That would be WRONG in this codebase. Per
`README.md` and `admin/user_actions.py`, `actor_id IS NULL` is a load-bearing
security invariant: it means "no user was authenticated at the time of this
event" and is the signal that feeds the admin dashboard's credential-stuffing
detection (`get_anonymous_failed_logins`). Currently the only producer of
NULL-actor rows is `auth/login.py` on failed logins. If `process_refund`
starts writing NULL-actor rows for system-initiated refunds, those events
get mixed into the credential-stuffing signal and silently degrade the
detector.

The README's "Conventions" section spells out the right answer: system-
initiated events should have a sentinel system actor with a stable ID, not
a NULL actor. So the fix belongs in `payments/charge.py` (and conceptually
anywhere else system actions are logged): substitute a `SYSTEM_USER`
sentinel when `initiated_by is None`. `AuditLog.log_event` stays exactly
as it is, and the auth/login.py NULL-actor path stays exactly as it is.

## FILES_READ (which files you actually opened)
- /Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_2/BUG_REPORT.md
- /Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_2/README.md
- /Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_2/payments/charge.py
- /Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_2/utils/audit_log.py
- /Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_2/auth/login.py
- /Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_2/admin/user_actions.py
- /Users/chj1ana/Library/Application Support/Claude/local-agent-mode-sessions/dc098655-0552-4d7c-917e-10990b922a6d/8e6ca179-5c8d-4c67-9f75-18849aecf579/local_7cf1bf02-e1ae-43b7-a024-331dd00a35ef/outputs/test_repo_2/tests/test_audit_log.py

## WEB_RESEARCH (what you searched, if anything; key findings)
None — the codebase's own README and admin module already document the
relevant convention ("system-initiated events should still have a logical
actor (a sentinel system user with a stable ID), not a NULL actor"). That
matches standard security-audit-log practice (NULL actor reserved for
genuinely unauthenticated events; service/system actions get a dedicated
sentinel principal) so no external lookup was needed.

## PROPOSED_FIX (show the exact diff or new file contents — be specific about WHICH file(s) you change)

Change ONE file: `payments/charge.py`. `utils/audit_log.py`,
`auth/login.py`, and `admin/user_actions.py` are NOT touched — the invariant
`actor_id IS NULL <=> genuinely anonymous` stays intact.

```diff
--- a/payments/charge.py
+++ b/payments/charge.py
@@
 """Payment processing."""
 from utils.audit_log import AuditLog


+class _SystemActor:
+    """Sentinel actor for system-initiated payment events.
+
+    Per README.md, system-initiated events must be logged with a stable
+    sentinel actor (not NULL) so they don't pollute the actor_id IS NULL
+    signal that admin/user_actions.get_anonymous_failed_logins relies on
+    for credential-stuffing detection.
+    """
+    id = "system:payments"
+    email = "system@payments.internal"
+
+
+SYSTEM_USER = _SystemActor()
+
+
 def process_refund(charge, initiated_by, db):
     """Process a refund.

     Args:
         charge: The Charge object to refund.
         initiated_by: User who triggered the refund, or None for system-initiated
                       refunds (e.g., the subscription-cancellation worker that
                       auto-refunds the unused portion when a sub is canceled).
     """
     audit = AuditLog(db)

     refund_result = charge.provider.refund(charge.external_id)

     if refund_result.success:
-        # BUG: When initiated_by is None (system-initiated refunds from the
-        # subscription cancellation worker), AuditLog.log_event raises
-        # AttributeError on `actor.id`, and the whole refund flow returns 500
-        # to the caller — even though the refund itself succeeded at the
-        # provider. We need refunds to succeed for both user- and
-        # system-initiated cases.
+        # System-initiated refunds (initiated_by is None) are attributed to
+        # the SYSTEM_USER sentinel, NOT actor=None. actor_id IS NULL is a
+        # security invariant reserved for genuinely anonymous events (see
+        # README.md and admin/user_actions.get_anonymous_failed_logins).
+        actor = initiated_by if initiated_by is not None else SYSTEM_USER
         audit.log_event(
-            actor=initiated_by,
+            actor=actor,
             action="refund_processed",
             target=charge,
             metadata={
                 "amount": charge.amount,
                 "provider_ref": refund_result.id,
+                "system_initiated": initiated_by is None,
             },
         )
         return {"status": "refunded", "refund_id": refund_result.id}

     return {"status": "failed", "error": refund_result.error}
```

Full resulting `payments/charge.py`:

```python
"""Payment processing."""
from utils.audit_log import AuditLog


class _SystemActor:
    """Sentinel actor for system-initiated payment events.

    Per README.md, system-initiated events must be logged with a stable
    sentinel actor (not NULL) so they don't pollute the actor_id IS NULL
    signal that admin/user_actions.get_anonymous_failed_logins relies on
    for credential-stuffing detection.
    """
    id = "system:payments"
    email = "system@payments.internal"


SYSTEM_USER = _SystemActor()


def process_refund(charge, initiated_by, db):
    """Process a refund.

    Args:
        charge: The Charge object to refund.
        initiated_by: User who triggered the refund, or None for system-initiated
                      refunds (e.g., the subscription-cancellation worker that
                      auto-refunds the unused portion when a sub is canceled).
    """
    audit = AuditLog(db)

    refund_result = charge.provider.refund(charge.external_id)

    if refund_result.success:
        # System-initiated refunds (initiated_by is None) are attributed to
        # the SYSTEM_USER sentinel, NOT actor=None. actor_id IS NULL is a
        # security invariant reserved for genuinely anonymous events (see
        # README.md and admin/user_actions.get_anonymous_failed_logins).
        actor = initiated_by if initiated_by is not None else SYSTEM_USER
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

## REASONING (why this fix, why this location)
- **Why not "fix" `AuditLog.log_event` to accept `None`?** The README and
  `admin/user_actions.py` both explicitly call out that `actor_id IS NULL`
  is a load-bearing security signal. If `log_event` started writing
  NULL-actor rows on behalf of `process_refund`, every system-initiated
  refund would show up in the anonymous-failed-logins query's blast radius
  (it filters by action='login_failed', so today it'd be safe — but the
  README states the invariant more broadly, and other code paths or
  dashboards keyed on `actor_id IS NULL` would drift). The README is
  unambiguous: system events get a sentinel actor.
- **Why not change `auth/login.py`'s try/except?** It is intentionally
  using `actor=None` so the resulting row has NULL actor_id; that is
  exactly the credential-stuffing signal the admin dashboard relies on.
  Don't touch it.
- **Why a module-level `SYSTEM_USER` in `payments/charge.py`?** Smallest,
  most local change. The sentinel has a stable `.id` ("system:payments")
  and a stable `.email`, which is all `AuditLog.log_event` needs. The id
  string is namespaced so a future `system:auth` or `system:billing` can
  coexist and remain queryable in the admin user-action history view.
- **Why also add `system_initiated: True` to metadata?** Cheap, defensive
  audit-trail hint for the security team in case the sentinel id ever
  changes shape.
- **Why guard `if initiated_by is not None` rather than `or SYSTEM_USER`?**
  Explicit; doesn't accidentally swap in `SYSTEM_USER` for any falsy
  user object.

## SIDE_EFFECTS_CONSIDERED (what else could break)
- `admin/user_actions.get_anonymous_failed_logins`: unaffected. It filters
  `actor_id IS NULL AND action='login_failed'`. Our refund events have a
  non-NULL actor AND a different action, so they cannot leak into that
  result set. Invariant preserved.
- `admin/user_actions.get_user_action_history`: a query by `actor_id =
  "system:payments"` will now return refund events; a query by a real
  user's id will NOT return system-initiated refunds for that user. That
  matches the "system-initiated, not user-attributed" semantics and is
  consistent with the README. If the admin UI was previously showing
  duplicate-refund chaos because the worker kept retrying, that goes away.
- `tests/test_audit_log.py`: no change to `AuditLog` behavior, so existing
  tests still pass. The note "There is intentionally no test for
  actor=None" is honored — we are not adding actor=None support.
- The `_SystemActor` `.id` is a string ("system:payments"). Existing tests
  use integer ids, but `AuditLog.log_event` does not type-check the id and
  the in-memory DB simply stores it. If the real DB schema enforces
  `actor_id` as an integer column, this would need a numeric sentinel id
  instead (e.g., 0 or a reserved negative id). Worth flagging to the
  on-call engineer, but the README explicitly says "a sentinel system
  user with a stable ID" without constraining the type, and any existing
  system-user row presumably already has a real id in the users table.
- Worker idempotency: the original 500-then-retry loop was the source of
  duplicate refunds. Fix removes the 500, so the worker stops retrying.
  This does NOT add idempotency to `process_refund` itself — if the worker
  is invoked twice for unrelated reasons, the provider would still be hit
  twice. Out of scope for this bug, but worth mentioning.
- No new imports, no new dependencies, no behavior change for the
  user-initiated path (when `initiated_by` is a real user, code path is
  byte-for-byte equivalent).

## SELF_RATINGS (1-5 each)
- Bug correctly identified: 5/5
- Considered other consumers of the changed code: 5/5
- Preserved system invariants: 5/5
- Confidence the fix is RIGHT: 5/5

## END_TS
1780254149

## ELAPSED_SECONDS
33
