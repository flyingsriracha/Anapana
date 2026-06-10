## REFLEX
Without this process, my answer would be a data-deletion checklist with GDPR compliance notes and a grace-period / soft-delete pattern — competent but blind to the B2B multi-actor ownership problem.

## TIER
FULL (T1: cross-system; T3: irreversible — either alone rounds up)

## ANSWER

The framing "delete my account" imports an individual-centric mental model into a shared-resource context. That tension is the actual design problem. Before writing a line of spec, resolve it — because the answer determines the entire branching structure of the feature.

---

**The actor split you need to resolve first**

In a B2B team account, "delete my account" means at least four different things depending on who's asking:

1. A regular member removing themselves from a team — seats, permissions, personal data
2. A team admin removing another user — same, plus audit trail
3. An account owner (billing holder) trying to leave — blocks unless ownership is transferred or the account is closed
4. An organization admin closing the entire account — full teardown of billing, integrations, all member data

These are not the same operation. Shipping them as one flow produces either a system that silently destroys shared state or one that blocks legitimate exits. Design the four paths first; the implementation can share steps underneath.

---

**The questions I'd ask before building**

*Ownership and access:*
- Can an account owner delete their personal account without closing the organization? If yes, what happens to the org?
- Who can trigger a full org closure — anyone with billing access, or only a specific "superadmin" role?
- What happens to content owned by the departing user (docs, integrations, API keys they created)? Reassign to another owner, orphan, or block deletion until resolved?

*Billing:*
- Does deletion cancel the subscription, or is that a separate flow? (If separate, you will have zombie subscriptions.)
- What is the refund / proration policy on mid-cycle deletion?
- Does the billing system (Stripe, etc.) need an explicit cancellation call, or does it infer from subscription status? Who owns that API call — your app or a manual CS step?

*Third-party integrations:*
- What integrations does this SaaS have, and which are OAuth-token-based vs. API-key-based?
- On user deletion, are those tokens revoked immediately, queued, or left to expire? If the revocation call fails, what is the recovery path?
- Do any integrations write back to your system (webhooks)? After deletion, those callbacks arrive to a dead entity — how do you handle them?

*Data and compliance:*
- Which jurisdictions are your customers in? GDPR (erasure within 30 days), CCPA, LGPD, others — each has a different timeline and scope obligation.
- What counts as "personal data" in your schema? User table rows are obvious; audit logs with names embedded, support tickets, email history in a third-party CRM — less obvious.
- What is your backup retention period? Erasure from the live DB is insufficient if backups are kept 90 days — you need a documented process for backup scrubbing or a legal basis to retain.
- Do you need to retain billing records for tax purposes after the account is gone? This is a real conflict with erasure — resolve it in your data classification policy first.

*Product experience:*
- What is the cooling-off period, if any? Many SaaS products use a 30-day soft-delete before hard erasure. Is that appropriate for your customer segment, or does enterprise compliance require faster erasure on request?
- Who receives notifications, and when? At minimum: the departing user (confirmation), affected team members (access warning), billing contact (subscription status).
- Is there an export step before deletion? GDPR requires you to provide data portability. Even if not legally required in your jurisdiction, removing this creates churn-friction and support tickets.

---

**How I'd structure the build**

Sequence matters more than completeness here. The worst outcomes come from shipping deletion as a single synchronous action when it's actually a multi-step, multi-system saga.

*Phase 1 — Define the four actor paths and their preconditions.* No code yet. Produce a decision table: actor × account state → allowed action / required prerequisite. This is the spec. Get it signed off.

*Phase 2 — Ownership transfer gate.* Before any delete path can complete for an owner or admin, force an explicit reassignment or org-close decision. This is a blocking UX step, not a warning. If the org has one owner and they try to self-delete, the path must hard-stop until they either promote another member or acknowledge they are closing the org.

*Phase 3 — The deletion saga, not a single transaction.* Steps in order:
1. Collect and export user data (offer download link, retained for N days)
2. Revoke all active sessions and OAuth tokens for the departing account
3. Disable integrations / API keys scoped to that user
4. Soft-delete the user record (mark inactive, preserve FK references)
5. Cancel or update billing (seat removal or subscription cancellation — synchronous call with confirmation)
6. Hard-delete / anonymize PII from live store after cooling-off period
7. Queue backup scrub per your retention policy

Each step should be logged to an immutable audit trail (even after deletion, you need to prove you complied). Steps 2 and 5 are the most dangerous if they fail silently — instrument them with explicit failure alerting, not just a catch-and-log.

*Phase 4 — Integration revocation hardening.* For each third-party integration: verify the revocation call succeeded, retry with backoff, and surface a manual remediation path if it fails after N retries. "Token expired naturally" is not an acceptable substitute for explicit revocation when you're handling a security-sensitive off-boarding.

---

**The tensions worth naming**

- **Erasure vs. audit integrity.** You are legally required to erase PII; you may also be legally required to retain financial records and may contractually require audit logs. These conflict. Resolution: anonymize rather than delete where retention is required — replace name/email with a pseudonymous ID, retain the record structure.

- **Speed vs. safety.** Self-service immediate deletion is the best UX. It is also the highest-risk path for accidental org destruction. The right balance for B2B: self-service for member self-removal, CS-gated or multi-step confirmation for account owner closure and org closure.

- **Soft-delete as compliance theater.** Soft-delete is useful for accidental deletion recovery. It does not satisfy GDPR erasure if PII remains queryable. Do not conflate the two in your data model.

- **Third-party state you don't control.** OAuth tokens issued by your app to a third party (e.g., a Zapier integration) can be revoked on your side; tokens issued by the third party to the user's account cannot. Know which direction each integration flows before committing to a "full revocation" promise.

---

**What I'd ship last, not first**

A self-service "delete everything immediately" button for account owners. This is the highest-leverage failure mode — org owner misclicks, entire company loses access. Implement member self-removal first (lower blast radius), validate the saga pipeline, then layer in org-closure with mandatory confirmation steps and a time delay.

## END_TS
1780599373
