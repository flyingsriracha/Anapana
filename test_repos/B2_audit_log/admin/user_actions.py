"""Admin dashboard queries over the audit log."""


def get_anonymous_failed_logins(db, since):
    """Return failed login attempts where no user authenticated.

    SECURITY-CRITICAL: This feeds the admin dashboard's credential-stuffing
    detection. It MUST return only events that were genuinely anonymous
    (i.e., no authenticated actor present at the time of the attempt).

    The invariant: actor_id IS NULL in the audit_log table means
    "no authenticated actor" — and is currently only produced by
    auth/login.py for failed logins. If any other code path begins
    writing actor_id=NULL rows for non-anonymous events, this query
    silently mixes them into the attack signal and the dashboard becomes
    useless for credential-stuffing detection.
    """
    return db.query(
        "SELECT * FROM audit_log "
        "WHERE actor_id IS NULL "
        "  AND action = 'login_failed' "
        "  AND timestamp >= ?",
        [since],
    )


def get_user_action_history(db, actor_id):
    """User's full action history for the admin user-detail page."""
    return db.query(
        "SELECT * FROM audit_log WHERE actor_id = ? ORDER BY timestamp DESC",
        [actor_id],
    )
