## REFLEX
Design the account deletion flow with soft-delete, data retention windows, billing cancellation, and a confirmation gate.

## TIER
T2+T3 (framing pressure: "greenfield/no spec" suppresses constraint-finding; hard to reverse)

## ANSWER

The first and most important thing to nail before writing a line of spec: "delete my account" means two completely different features in a B2B team product, and conflating them will produce the wrong thing.

**The fork you need to resolve first**

- *Member leaving a team* — a user removes themselves from an organization. The org account survives; the user's personal login may or may not persist; their data (docs, comments, audit trail) stays in the org.
- *Owner deleting the organization* — the billing entity and all its members, data, and integrations are destroyed. This is the catastrophic path.

Every design decision downstream branches on this. What follows covers both, but you need to pick which one is in scope for the first release and spec them separately.

---

**Considerations and tensions**

*Data ownership and portability*
- GDPR/CCPA give the *individual* the right to erasure of personal data, but the *organization* may have a legitimate interest in retaining business records (audit logs, financial history, content created in their workspace).
- These two rights conflict. The usual resolution: anonymize PII in retained records rather than hard-delete. You need legal sign-off on what counts as "deletion" in your jurisdiction before building.
- Export-before-delete is a user-expectation baseline. If you skip it, expect support tickets and potential regulatory exposure.

*Billing*
- Cancellation ≠ deletion. A user who clicks "delete account" probably expects billing to stop; your billing provider (Stripe, etc.) doesn't care unless you explicitly cancel the subscription.
- Proration, outstanding invoices, and annual-plan refund policy all need explicit decisions. The deletion flow must either block until billing is resolved or trigger cancellation atomically.
- If the org is on a team plan with seats, deleting one member affects seat count; deleting the org needs to cancel the subscription, not just the account record.

*Third-party integrations*
- OAuth tokens granted to third-party apps need to be revoked. If you soft-delete and tokens survive, the deleted account can still be used as an identity surface by external apps.
- Outbound integrations (webhooks, Slack, Jira, SSO providers) need to be deprovision-notified or they'll keep sending/receiving data to a dead endpoint.
- Any API keys the org issued should be invalidated immediately, not on a delay.

*Team continuity*
- If the last owner of an org deletes themselves, the org is now ownerless. You need either a forced ownership transfer gate or an auto-suspend path before allowing deletion.
- Member data (files, comments, tasks) is often load-bearing for other users. Deciding what happens to it (reassign to a "deleted user" tombstone, delete, or reassign to the owner) is a product decision that must be explicit.

*Soft-delete vs. hard-delete*
- Soft-delete (mark as deleted, purge after N days) is almost always the right first move. It gives a recovery window for accidental deletions and satisfies most retention requirements.
- Set and communicate the purge window explicitly (7 days? 30 days?). Users need to know what the window is; support needs to know what they can recover.
- Hard-delete should require a secondary deliberate confirmation and, for orgs, probably an async job with a delay.

*Reversibility and confirmation UX*
- High-consequence actions warrant friction: type-to-confirm ("type your organization name"), not just a checkbox.
- Send an email confirmation *before* initiating deletion, and a second email when purge completes.
- Provide a grace-period cancellation link in the first email.

*Audit and compliance*
- You likely need to retain the fact that a deletion occurred (who, when, what scope) even if you delete the content. The audit event is not PII in the same way the content is.
- Financial records (invoices, payment history) may have mandatory retention periods (7 years in many jurisdictions) independent of the user's deletion request.

---

**Questions I'd ask before building**

1. **Scope for v1:** member self-removal, or org deletion, or both? (They're different features.)
2. **What does "deleted" mean legally?** Has your legal/privacy team defined which data must be purged vs. anonymized vs. retained?
3. **What happens to the deleted user's content?** Who owns it after they're gone?
4. **Last-owner safeguard:** what's the policy if the sole org owner initiates deletion?
5. **Billing ownership:** does deletion trigger immediate cancellation, or does the subscription run to end-of-period?
6. **Recovery window:** is there a grace period during which an admin can restore the account? What's the SLA for support-assisted recovery?
7. **Integration deprovisioning:** do you have a registry of all active OAuth grants and webhooks per org, or does that need to be built first?
8. **Regulatory jurisdiction:** which data-privacy regimes apply to your customer base, and have you confirmed your soft-delete + anonymize approach satisfies them?
9. **Notification chain:** who gets notified (the deleting user, other org members, the billing contact)? Are those the same person?
10. **Deletion initiated by whom?** Can an org admin force-remove a member? Can your support team delete an org on a customer's behalf?

The instinct to start designing a deletion flow is right, but the biggest risk is building the member-removal flow when the org-deletion flow is what customers mean (or vice versa). Lock that fork first.

## END_TS
1780599371
