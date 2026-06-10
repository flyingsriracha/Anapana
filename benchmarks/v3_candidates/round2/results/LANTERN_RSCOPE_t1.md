## REFLEX
Without a careful process, my answer would be: add a soft-delete with a 30-day grace period, a confirmation email, and a data export button — because that's the standard B2C pattern, and it feels complete.

## TIER
STANDARD (T2: framing suppresses the B2B complexity; T3: data deletion is irreversible)

## ANSWER

The first thing to nail is that "delete my account" in B2B SaaS is not one problem — it's at least three overlapping problems that have different answers, and conflating them is how you ship something that's technically functional but operationally disastrous.

**The three problems you're actually solving:**

1. **Identity removal** — remove a person's login, credentials, and personal data from the system
2. **Entitlement unwinding** — resolve what they owned: seats, subscriptions, billing authority, integrations
3. **Data lifecycle** — decide what happens to content they created that other people depend on

Almost every B2B "delete account" incident I've seen (ghost seats still billing, integrations silently breaking, org owners locked out) traces back to treating these as one thing.

---

**The hardest tensions to resolve before you write a line of code:**

**Member vs. org deletion.** In a team account model, "delete my account" can mean "remove me from this org" or "shut down the entire organization." These are completely different operations with different authorization requirements and different blast radii. You need a clear model for which one the user is actually requesting, and the UI must make it unambiguous. Most B2B products have two separate paths: leave/deactivate (member-level) and cancel/delete (org-level), and they enforce who can do which.

**Billing ownership transfer is a hard prerequisite.** If the user being deleted is the billing owner, you cannot let deletion proceed until billing authority transfers to another admin. If you don't gate on this, you'll have orgs where the subscription belongs to a deleted user — some billing systems will continue charging a ghost; others will lapse. Either outcome is bad. The billing transfer step needs to happen *before* the deletion flow completes, not as a post-deletion cleanup task.

**Shared content ownership.** Documents, projects, comments, and audit logs created by the user don't belong only to them in a team context. You need a policy decision (not a technical one) before you build: do shared objects get reassigned to a team admin, anonymized, or deleted? Each has tradeoffs. Reassignment is safest for team continuity but may surprise the user who expected their data to disappear. Anonymization satisfies privacy intent but breaks attribution. Deletion can break other users' work. There is no universally correct answer — the business has to decide, and the decision should be documented and surfaced to users before they confirm.

**Third-party integration revocation.** If the user authenticated integrations (Slack, Salesforce, Zapier, whatever) under their identity, those OAuth tokens persist after account deletion unless you explicitly revoke them. Stale tokens either continue functioning (a security problem) or fail noisily (an ops problem for the team). Before building, you need an integration inventory and a revocation path for each. This is the most commonly skipped step.

**Legal: right to erasure vs. retention obligations.** GDPR Art. 17 gives users a right to erasure, but Art. 17(3) carves out exceptions for legal obligations and contractual performance. In B2B, the org may have a retention policy that conflicts with a member's deletion request. You need a legal/compliance call on this before building — it determines whether you do hard delete, anonymization, or a hybrid. CCPA has similar structure; if you have users in California, it applies. If you have international users, you may be juggling multiple jurisdictions simultaneously.

**Grace period and data export.** A 30-day soft-delete with a data export step is not just good UX — for GDPR/CCPA, a DSAR (Data Subject Access Request) export before deletion is effectively required if the user asks for it. Build the export capability first; it's also useful for support and debugging regardless of deletion.

---

**Questions I'd want answered before writing a spec:**

1. Who can initiate org-level deletion vs. member-level removal? Is it any member, admins only, or the billing owner only? This determines the authorization model for the entire flow.

2. What is the data retention policy for audit logs and financial records? Legal and finance need to answer this — it determines whether "delete" means hard delete, anonymization, or a tiered approach.

3. Do any of your third-party integrations authenticate at the user level (individual OAuth) vs. the org level (org-wide API key)? This scopes the revocation work. If all integrations are org-scoped, this problem is smaller.

4. What happens to annual contracts mid-term? Deletion during an active annual contract period has billing and contractual implications that the product alone can't resolve — it needs a policy from finance/legal.

5. Do you have any compliance frameworks (SOC 2, HIPAA, ISO 27001) that impose specific data retention or deletion audit requirements? These constrain the implementation significantly.

6. What's the expected volume and user sentiment around this feature? "Delete my account" in B2B is often triggered by churn or a security concern. If it's churn, there may be a save/offboard flow worth designing. If it's a security incident (compromised account), the deletion path needs to be fast and not require transferring ownership — those are different UX requirements.

---

**Rough implementation sequence once the above is resolved:**

Phase 1: Member self-removal (leave org, revoke own sessions and API keys, anonymize or transfer personal data per policy). This is lower risk and affects only the leaving user.

Phase 2: Org-level deletion (admin/billing owner only, requires billing owner transfer gate, 30-day grace period with reactivation, data export on request, integration revocation, then async hard delete with audit log of what was deleted and when).

Phase 3: Compliance tooling — a deletion audit trail, a DSAR export endpoint, and an internal admin view for support to verify deletion completed (you'll need this for regulatory inquiries).

Don't build Phase 2 without the policy answers from legal/finance. Shipping Phase 1 first gets you value quickly and surfaces edge cases in the data model before the irreversible operation.

## END_TS
1780599384
