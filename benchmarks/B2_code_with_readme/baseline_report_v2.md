## START_TS
1780283278

## DIAGNOSIS
`AuditLog.log_event` in `utils/audit_log.py` unconditionally accesses `actor.id` and `actor.email` on lines 23-24. When `process_refund` in `payments/charge.py` is called with `initiated_by=None` (system-initiated refund), this raises `AttributeError: 'NoneType' object has no attribute 'id'`. The refund itself succeeds at the payment provider (line 16 runs fine), but the crash on the audit log call causes the function to return a 500, which triggers retries and duplicate refunds.

The README adds a critical architectural concern: `actor_id IS NULL` in the audit_log table means "genuinely anonymous event" (no authenticated user present). This is used by `admin/user_actions.get_anonymous_failed_logins` for credential-stuffing detection. The README explicitly states: "System-initiated events should still have a logical actor (a sentinel system user with a stable ID), not a NULL actor."

Therefore the correct fix has two parts:
1. Fix `audit_log.py` to handle `actor=None` gracefully (producing NULL actor_id — valid for genuinely anonymous events like failed logins).
2. Fix `charge.py` to pass a sentinel system actor object rather than None for system-initiated refunds — preserving the invariant that NULL = anonymous, non-NULL system ID = automated/system.

Additionally, `auth/login.py`'s try/except workaround can be removed since it was a temporary patch for the now-fixed crash.

## FILES_READ
- `/tmp/B2_audit_log_buggy/BUG_REPORT.md`
- `/tmp/B2_audit_log_buggy/payments/charge.py`
- `/tmp/B2_audit_log_buggy/utils/audit_log.py`
- `/tmp/B2_audit_log_buggy/README.md`
- `/tmp/B2_audit_log_buggy/auth/login.py`
- `/tmp/B2_audit_log_buggy/admin/user_actions.py`
- `/tmp/B2_audit_log_buggy/tests/test_audit_log.py`

## WEB_RESEARCH
None — the bug and fix were fully diagnosable from the codebase and README.

## REPRODUCTION
none — diagnosed from code only

The crash path is deterministic: `process_refund(charge, initiated_by=None, db)` -> `audit.log_event(actor=None, ...)` -> `actor.id` on line 23 of `audit_log.py` -> `AttributeError`.

## DOC_LED_FLAG
doc-led — the README was read before finalizing the fix. It established the critical invariant about NULL actor_id meaning "anonymous", which changed the fix from "just handle None in audit_log.py" to "use a sentinel system actor in charge.py + fix audit_log.py". Without reading the README, the naive fix (allow None in audit_log.py, write NULL for system refunds) would have violated the documented convention, even if it technically would not contaminate the current admin query (which also filters on action = 'login_failed').

## PROPOSED_FIX

### File 1: `utils/audit_log.py` — handle `actor=None` gracefully

```diff
--- a/utils/audit_log.py
+++ b/utils/audit_log.py
@@ -20,8 +20,10 @@ class AuditLog:
         record = {
-            "actor_id": actor.id,
-            "actor_email": actor.email,
+            "actor_id": actor.id if actor is not None else None,
+            "actor_email": actor.email if actor is not None else None,
             "action": action,
             "target_id": target.id,
             "metadata": metadata or {},
             "timestamp": datetime.utcnow(),
         }
         self.db.insert("audit_log", record)
```

### File 2: `payments/charge.py` — use a sentinel system actor instead of passing None

```diff
--- a/payments/charge.py
+++ b/payments/charge.py
@@ -1,7 +1,21 @@
 """Payment processing."""
 from utils.audit_log import AuditLog
 
 
+class _SystemActor:
+    """Sentinel actor for system-initiated events (no human user present).
+
+    Produces a stable non-NULL actor_id in the audit log, distinguishing
+    automated system events from genuinely anonymous events (actor_id IS NULL).
+    This preserves the audit log invariant documented in README.md:
+    NULL actor_id = anonymous (e.g., failed login); non-NULL = identified actor.
+    """
+    id = "system"
+    email = "system@internal"
+
+
+_SYSTEM_ACTOR = _SystemActor()
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
+    actor = initiated_by if initiated_by is not None else _SYSTEM_ACTOR
 
     refund_result = charge.provider.refund(charge.external_id)
 
     if refund_result.success:
         audit.log_event(
-            actor=initiated_by,
+            actor=actor,
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

### File 3: `auth/login.py` — remove the try/except workaround (now that audit_log.py handles None)

```diff
--- a/auth/login.py
+++ b/auth/login.py
@@ -19,16 +19,9 @@ def handle_login(email, password, db):
     if not user or not user.check_password(password):
-        # Failed login from no authenticated user. We want to log this with
-        # actor=None so the admin "anonymous failed logins" view can flag
-        # credential-stuffing attacks (see admin/user_actions.py).
-        #
-        # KNOWN ISSUE: AuditLog.log_event currently crashes on actor=None.
-        # We swallow the AttributeError as a temporary workaround. The
-        # auditing of these events is best-effort until the upstream
-        # function supports None actors.
-        try:
-            audit.log_event(
-                actor=None,
-                action="login_failed",
-                target=_FailedLoginTarget(email),
-            )
-        except AttributeError:
-            pass
+        # Failed login — actor=None produces actor_id IS NULL in audit_log,
+        # which is the signal for get_anonymous_failed_logins credential-stuffing detection.
+        audit.log_event(
+            actor=None,
+            action="login_failed",
+            target=_FailedLoginTarget(email),
+        )
         return {"error": "Invalid credentials"}, 401
```

## REASONING
The bug has a surface fix and a subtle architectural concern:

**Surface fix**: `audit_log.py` crashes because it unconditionally dereferences `actor.id` and `actor.email` without checking for None. Adding a None guard fixes the crash.

**Architectural concern (from README)**: The NULL actor_id value is semantically loaded — it means "genuinely anonymous, no authenticated user". The README explicitly says system-initiated events should use a sentinel user with a stable ID. The `_SystemActor` sentinel in charge.py implements this convention.

The fix in `audit_log.py` is still needed: (a) the log_event docstring already says actor "May be None for unauthenticated attempts", (b) auth/login.py is a legitimate None caller, (c) the try/except in auth/login.py was masking failed-login events so they were never actually logged — removing it is a security improvement.

## SIDE_EFFECTS_CONSIDERED
1. **Credential-stuffing dashboard**: `get_anonymous_failed_logins` queries `actor_id IS NULL AND action = 'login_failed'`. System-initiated refund events have `action = 'refund_processed'`, so even a NULL actor_id there would not contaminate the signal. But using a sentinel actor is cleaner and matches the documented convention.
2. **`auth/login.py` workaround removal**: Removing the try/except means failed-login events now reliably appear in the audit log (previously they were silently dropped). This is a security observability improvement, not a regression.
3. **Existing callers of `log_event`**: All non-None callers are unaffected — the ternary is a no-op for non-None actors.
4. **`get_user_action_history`**: Queries by actor_id. System actor id = "system" (string), so audit records for system-initiated refunds are correctly queryable.
5. **Duplicate refunds**: The crash after `charge.provider.refund` caused the worker to get a 500 and retry, creating duplicate charges. The fix prevents the crash so a 200 is returned and retries are not triggered.
6. **Database schema**: If `actor_id` has a foreign key constraint to a users table, the string "system" would violate it. This is not visible in the codebase. If that constraint exists, a proper system user row in the users table would be needed. This is the main residual uncertainty.

## IDENTITY_CHECK
No — this was not purely my reflex. The naive reflex fix would have been to just add `if actor is not None` guards in `audit_log.py` and call it done. Reading the README changed the approach: the sentinel actor in `charge.py` was doc-led. Without reading the README, I would have passed None through to audit_log.py (technically safe given the admin query's additional action filter, but violating the documented convention). The three-file fix emerged from careful reading of the docs.

## SELF_RATINGS (1-5 each)
- Root cause / surface bug identified: 5/5
- Considered all consumers of the changed code: 5/5
- Preserved system invariants: 5/5
- Confidence the fix is RIGHT: 4/5

(One point off on confidence: the sentinel actor id/email values "system"/"system@internal" are reasonable but the codebase may have a foreign key constraint on actor_id referencing a users table. The architecture is correct; the exact sentinel values may need adjustment for the real DB schema.)

## END_TS
1780283327

## ELAPSED_SECONDS
49
