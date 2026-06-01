"""Audit log for security-sensitive actions.

Used across payments, auth, and admin modules. See README.md for invariants.
"""
from datetime import datetime


class AuditLog:
    def __init__(self, db):
        self.db = db

    def log_event(self, actor, action, target, metadata=None):
        """Log an audit event.

        Args:
            actor: User object performing the action. May be None for unauthenticated
                   attempts (e.g., failed login from no logged-in user).
            action: String describing the action (e.g., 'login_failed', 'refund_processed').
            target: The entity being acted upon. Must have an `.id` attribute.
            metadata: Optional dict of additional context.
        """
        record = {
            "actor_id": actor.id,
            "actor_email": actor.email,
            "action": action,
            "target_id": target.id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow(),
        }
        self.db.insert("audit_log", record)
