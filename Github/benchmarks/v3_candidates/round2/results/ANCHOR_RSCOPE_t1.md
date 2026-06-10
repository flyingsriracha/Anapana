## REFLEX
My gut answer right now is: delete account for B2B SaaS is mostly a legal/data compliance problem dressed up as a UX feature — the hard part is what happens to shared team data, not the account row itself.

## TIER
T1 (shared resource) + T3 (hard to roll back) → frame check applied

## ANSWER

Before writing a line of code, I'd want to nail one disambiguation: are we talking about a **user-seat deletion** (one person leaving a team) or an **org/account deletion** (the company canceling)? These are different products with different blast radii, different legal obligations, and different UX surfaces. A lot of "delete my account" features ship broken because the team conflated the two.

---

### The questions I'd ask first

1. **Who can trigger this?** Only the account owner? Any admin? Any member for their own seat?
2. **What does "my account" mean to the user?** Their personal login, or the whole org subscription?
3. **Do we have GDPR/CCPA obligations?** If we serve EU or California users, deletion isn't optional UX — it's a legal requirement with a 30-day clock (GDPR Art. 17).
4. **What's the data ownership model?** Does content a user created belong to them, to the org, or is it ambiguous? (Docs, comments, audit trails, billing history.)
5. **What happens to the org if the sole owner deletes?** Is that even allowed? Does ownership need to transfer first?
6. **Billing state?** Mid-cycle cancellation, proration, outstanding invoices, annual contract — does deletion immediately cancel or schedule for period-end?
7. **Third-party integrations?** OAuth tokens, webhooks, API keys scoped to that user or org — what revokes, what breaks for downstream systems?
8. **Reversibility window?** Soft-delete with a 30-day grace? Immediate hard delete? This is a product decision with serious support-cost implications.

---

### The real design surface

**User-seat deletion (one person leaving)**

The core tension: their data is entangled with the org's data. You can delete their login credential and PII, but you probably cannot purge every record they touched without corrupting team history. Most teams land on: anonymize the actor ("Deleted User"), retain the content, revoke their auth tokens and integration access.

What to build:
- Reassign or orphan any resources they own (projects, pipelines, billing contacts)
- Force ownership transfer if they're the last admin
- Revoke all active sessions, API keys, OAuth grants scoped to them
- Queue a PII scrub job (name, email, profile data) — don't do it synchronously in the request
- Emit a deletion audit event; retain it for legal/compliance even after PII scrub
- Trigger offboarding for connected integrations (Slack deactivation, SSO deprovisioning if SCIM)

**Org/account deletion (company canceling)**

Higher stakes. Key considerations:

- **Last-chance data export must come first.** Never let a user nuke an org without a clear path to export everything they'd lose. If you don't build this, support will build it for you, badly, under pressure.
- **Billing must settle before deletion completes.** Outstanding invoices, active subscription — don't let the account row disappear while Stripe still thinks they're a customer.
- **Cascading third-party state.** Every OAuth app the org authorized, every webhook endpoint you call, every API key you issued — you need a revocation sweep. Missing this is how you get ghost orgs that still receive webhook callbacks years later.
- **Soft-delete with a grace period is almost always correct for orgs.** 30 days lets you recover from accidental deletion without a DBA intervention. Hard-delete at grace-period expiry via a background job.
- **Legal hold carve-out.** If you're in a regulated space or have any enterprise contracts, some data cannot be deleted on demand regardless of user request. Flag this before the feature ships.

---

### The tensions worth naming

- **"Right to erasure" vs. audit trail integrity.** You may be legally required both to delete PII and to retain audit logs. The resolution is anonymization, not deletion, for log records — but this needs a lawyer's sign-off, not an engineer's assumption.
- **Soft delete vs. hard delete.** Soft delete is safer operationally but complicates "am I actually deleted?" for the user, and GDPR's right to erasure doesn't care about your soft-delete flag.
- **Immediate vs. scheduled.** Immediate feels clean; scheduled gives a recovery window. The right call depends on your churn rate and support capacity.
- **Who notifies downstream systems?** If the org had a Salesforce integration and the org deletes, does Salesforce know? Does it matter? Figure this out before it becomes a support ticket.

---

### What I'd not build yet

An elaborate multi-step wizard with "type your org name to confirm" is tempting but premature. Build the data model and cascade logic correctly first. The UX can be layered after. The inverse — beautiful UX on top of incomplete cascade logic — is how you end up with zombie accounts.

---

### Proposed next step

Sketch the entity-relationship of what gets deleted, anonymized, or retained for each actor type. Put it in front of legal, support, and at least one enterprise customer before writing code. This is the 1-hour artifact that prevents 3 months of rework.

## END_TS
1780599359
