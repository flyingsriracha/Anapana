## REFLEX
Without deliberation, I'd propose a multi-step confirmation wizard: verify identity, show data-to-be-deleted summary, 30-day grace period, hard delete — with GDPR as the main driver and the key question being org-level vs. member-level account ownership.

## TIER
FULL (T1: billing/auth/integrations span multiple systems; T2: "greenfield/no spec" nudges away from constraints, which is where the real risk lives; T3: deletion is irreversible by design)

## ANSWER

**What "delete my account" actually means in a B2B team context is the first design decision, not the last.**

There are at least three distinct entities a user might mean: their personal membership in a team, the entire team/org account, or both. The delete flow, the legal obligations, and the engineering surface area are entirely different for each. This is the first question to answer before writing a line of spec.

---

### The hard constraints that shape everything else

**Legal/compliance surface — leads the design, not the UX:**
- GDPR/CCPA right-to-erasure applies to personal data, not business records. You must know what is "personal data" vs. "org-owned business data" in your schema before you can honor deletion requests correctly.
- Some data cannot be deleted regardless of user request: financial transaction records (typically 7 years), audit logs required by SOC 2 or contractual obligations, data subject to a legal hold.
- B2B contracts with customers may specify data retention terms. Check before assuming you can delete on request.
- If you process data on behalf of your B2B customer (you're a data processor, they're the controller), the individual user may not have standing to demand deletion — their employer's contract governs. You need a clear policy on this.

**Billing:**
- An account deletion request mid-billing cycle raises immediate questions: do you prorate? Refund? Honor to end of period? This is a policy decision, but it must be made before build — otherwise billing and deletion get out of sync and you get chargebacks and support escalations.
- Active subscription must be cancelled before or atomically with deletion. Orphaned subscriptions (deleted account, live subscription) are a known failure mode that causes ongoing charges post-deletion.
- If the customer is on an annual contract with an SLA or penalty clause, self-serve deletion may need to be gated.

**Third-party integrations:**
- OAuth tokens granted to third parties do not self-expire on account deletion. Revoke them explicitly, or integrations will continue making authenticated API calls with stale credentials against a deleted account — a security hole.
- Third-party integrations may hold copies of your user's data (Slack, Salesforce, GitHub, etc.). Deletion in your system does not cascade to theirs. You need to document this clearly in your privacy policy and ideally surface it in the deletion flow.
- Your own webhooks/event streams: if integrations are subscribed to user events, deletion must notify them cleanly, not just stop emitting.

---

### The team account topology problem

In a multi-user org account, you need explicit rules for:
- **Last admin / sole owner**: if the deleting user is the only admin or owner of a team account, what happens? Block deletion until ownership is transferred? Auto-delete the whole org? This is a critical branch the UX must surface.
- **Active seats and billing**: other team members' access is tied to the org subscription. Deleting the org owner without notifying members creates a support disaster.
- **Data ownership**: content created by a user within an org — does it belong to the user or the org? Your answer determines what gets deleted vs. reassigned vs. orphaned.

---

### The deletion flow itself

Given the above, a well-designed flow looks like:

1. **Intent capture**: "Delete my membership from [Org]" vs. "Delete my personal account" vs. "Delete [Org] and all its data" — these are different flows. Don't merge them.

2. **Pre-deletion blockers (surfaced, not silently prevented)**:
   - Ownership transfer required if last admin
   - Active subscription status and what deletion means for billing
   - Any pending actions (invoices, in-flight data exports, active API sessions)

3. **Disclosure, not just confirmation**: Show the user what will actually happen — what gets deleted, what gets retained (and why, with legal basis), what integrations will be affected, what teammates will lose access to. This serves both UX and legal (documented informed consent).

4. **Grace period with genuine reversibility**: 14–30 days is standard. During this window, the account is suspended (login blocked, integrations revoked, billing cancelled) but data is not yet purged. This window should be clearly communicated, and the user should receive an email with the exact purge date.

5. **Hard delete with audit trail**: The actual data purge should be logged (what was deleted, when, by whom) even if the content is gone. You may need this for legal defense. Log entries survive deletion; content doesn't.

6. **Confirmation to user and, if org-deletion, to all members**: email confirmation to the deleted account's address (for their records) and, if team-level, notification to all affected members with timeline.

---

### Tensions to resolve explicitly (don't leave these to implementation)

| Tension | Why it matters |
|---|---|
| Right to erasure vs. retention obligations | Some data legally cannot be deleted. You need a clear classification schema before build. |
| Self-serve vs. contract-gated | Annual contracts, enterprise tiers, or SLA customers may need human-in-the-loop deletion, not just a button. |
| Instant revocation vs. integration stability | Revoking tokens immediately is correct security posture; it may break live integrations the user forgot about. Consider a short notification window. |
| Org data vs. personal data | Same row in a database may contain both. Schema-level separation or clear tagging is load-bearing infra — retrofit is painful. |
| Member deletion vs. org deletion | UX that conflates these causes catastrophic misclicks. Separate flows, separate permissions, separate confirmation copy. |

---

### Questions to answer before building

1. **Who is the legal data controller for team-generated content** — the user or the org? This is the single most load-bearing legal question.
2. **What data categories exist in your schema**, and which ones are personal data, business records, or legally retained? Do you have a data map?
3. **What are your contractual obligations** to enterprise/annual customers on data retention? Do they get a separate deletion process?
4. **What does your billing system require** to cancel a subscription atomically? Can your billing provider handle mid-cycle cancellations cleanly?
5. **Which third-party integrations hold user data copies**, and do you have webhook endpoints to notify them? Have you audited this list?
6. **What is your OAuth revocation flow**, and do you have a token registry that lets you invalidate all tokens for a given user/org?
7. **What does "deleted" mean to your audit log system** — do those records survive, and do you have a legal basis to retain them?
8. **Is self-serve deletion available to all tiers**, or are enterprise/contract customers gated to support-assisted deletion?
9. **Who owns the deletion feature end-to-end** — does legal, product, and engineering all have a named owner? (Deletion features that span legal/billing/infra commonly stall at ownership gaps.)

---

### What I'd do first

Before any design work: pull a data map (or make one), get legal/compliance to classify each data type, and get a written policy decision on the org-vs-member ownership question. These three inputs constrain everything downstream. Building the UX without them means rebuilding it.

## END_TS
1780599384
