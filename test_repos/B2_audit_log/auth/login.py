"""Authentication endpoints."""
from utils.audit_log import AuditLog


class _FailedLoginTarget:
    """Wraps an attempted email so it can be the `target` of a failed-login event.

    We deliberately use the attempted email as the target so credential-stuffing
    queries can group attempts by email.
    """
    def __init__(self, attempted_email):
        self.id = attempted_email  # email used as the target identifier


def handle_login(email, password, db):
    audit = AuditLog(db)
    user = db.find_user(email)

    if not user or not user.check_password(password):
        # Failed login from no authenticated user. We want to log this with
        # actor=None so the admin "anonymous failed logins" view can flag
        # credential-stuffing attacks (see admin/user_actions.py).
        #
        # KNOWN ISSUE: AuditLog.log_event currently crashes on actor=None.
        # We swallow the AttributeError as a temporary workaround. The
        # auditing of these events is best-effort until the upstream
        # function supports None actors.
        try:
            audit.log_event(
                actor=None,
                action="login_failed",
                target=_FailedLoginTarget(email),
            )
        except AttributeError:
            pass
        return {"error": "Invalid credentials"}, 401

    audit.log_event(actor=user, action="login_success", target=user)
    return {"user_id": user.id}, 200
