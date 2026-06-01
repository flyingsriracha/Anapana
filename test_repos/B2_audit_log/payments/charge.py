"""Payment processing."""
from utils.audit_log import AuditLog


# Sentinel "system" actor for events that are not triggered by a human user
# (e.g., the subscription-cancellation worker auto-refunding the unused
# portion of a canceled subscription).
#
# Per README.md: system-initiated events MUST have a logical actor with a
# stable ID, NOT actor=None / actor_id=NULL. The audit log uses
# actor_id IS NULL as the signal for "genuinely anonymous event" (failed
# logins from no authenticated user), which feeds the admin dashboard's
# credential-stuffing detection. Writing actor_id=NULL rows for
# system-initiated refunds would dilute that signal.
class _SystemActor:
    id = "system"
    email = "system@internal"


SYSTEM_ACTOR = _SystemActor()


def process_refund(charge, initiated_by, db):
    """Process a refund.

    Args:
        charge: The Charge object to refund.
        initiated_by: User who triggered the refund, or None for system-initiated
                      refunds (e.g., the subscription-cancellation worker that
                      auto-refunds the unused portion when a sub is canceled).
                      When None, the audit event is attributed to the SYSTEM_ACTOR
                      sentinel rather than NULL — see module docstring.
    """
    audit = AuditLog(db)

    refund_result = charge.provider.refund(charge.external_id)

    if refund_result.success:
        # Normalize None to the system sentinel so the audit log gets a
        # queryable, distinguishable actor instead of crashing on actor.id
        # (and instead of writing actor_id=NULL, which would dilute the
        # credential-stuffing signal — see README.md).
        actor = initiated_by if initiated_by is not None else SYSTEM_ACTOR
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
