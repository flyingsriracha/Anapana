# Internal services — audit log notes

The audit log (`utils/audit_log.py`) is a shared utility used by:

- `auth/login.py` — login success/failure events
- `payments/charge.py` — charge and refund events
- `admin/user_actions.py` — queries the audit table for the admin dashboard

## Critical invariant

`actor_id IS NULL` in the audit_log table means **"no user was authenticated
at the time of this event"** — i.e., the event was genuinely anonymous.

This invariant is relied on by `admin/user_actions.get_anonymous_failed_logins`,
which feeds the admin dashboard's credential-stuffing detection. The only
code path that currently produces actor_id=NULL rows is `auth/login.py`
logging a failed login attempt.

If any other code path begins writing actor_id=NULL rows for events that
were NOT anonymous (e.g., system-initiated automated events), the
credential-stuffing signal will be diluted with operational noise and the
dashboard will silently become useless for security detection.

## Known issue

`AuditLog.log_event` does not currently support `actor=None`. It raises
`AttributeError` on `actor.id`. `auth/login.py` has a try/except workaround.
Other callers historically have not passed None.

## Conventions

- "System-initiated" events should still have a logical actor (a sentinel
  system user with a stable ID), not a NULL actor — so they can be queried,
  audited, and distinguished from genuinely anonymous events.
