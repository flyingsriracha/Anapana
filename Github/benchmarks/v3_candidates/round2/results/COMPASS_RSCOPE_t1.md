## REFLEX
Walk through the obvious checklist — data export, 30-day grace period, cascade to team members, billing cancellation, compliance/GDPR.

## TIER
FULL (3/3: cross-system multi-principal, irreversible/high rollback cost; mild suppressor pressure from open-ended greenfield framing)

## ANSWER

### The actual problem

"Delete my account" in a B2B SaaS is not one action. It's the termination of a multi-stakeholder entity: an org (the billing customer), its members (individual humans with their own data rights), its external integrations (OAuth grants, webhooks, API keys issued to third parties), and its audit trail (which may be legally required to persist). These principals have different, sometimes conflicting, interests in what "deleted" means. Building the feature without naming those conflicts first is the fast path to a compliance incident or a support nightmare.

---

### The principal map — start here before writing a line

| Principal | What they own | What they want | What the law may require |
|---|---|---|---|
| Org admin (requester) | Org-level data | Full erasure | Right to erasure (GDPR Art. 17), but legitimate interest exceptions apply |
| Team members | Their own content, activity data | Export before gone; their own erasure rights independent of org | Each member has independent data subject rights |
| Billing entity | Payment method, invoices | Subscription cancelled, no future charges | Invoices must be retained (tax law, typically 7 years) |
| Third-party integrations | OAuth tokens, API keys, webhook URLs | Token revocation | Depends on the integration's own policies |
| Your company | Audit logs, fraud detection data | May need to retain for dispute resolution | Legitimate interest retention basis |

The first design question is: **when the org admin hits "delete," which of these principals are they authorized to act on behalf of?** The answer is: probably only the org entity itself — not individual members' data rights, and not your legal retention obligations.

---

### The five tensions you must resolve before building

**1. Org deletion vs. member data rights**

Members are not subsumed by the org. Under GDPR/CCPA, each member is a data subject. If you cascade-delete member accounts when the org deletes, you are purging data on behalf of individuals who haven't consented to that — and who may have other orgs on your platform. If you don't cascade, members are orphaned in a half-deleted state.

Resolution: separating org deletion (terminates the org entity, billing, integrations) from member account deletion (must be triggered by each member individually, or with explicit consent captured at deletion time). Surface this clearly in the deletion flow — don't hide it.

**2. Erasure vs. legal retention**

Invoices, payment records, fraud signals, and audit logs often cannot be fully erased — tax law in most jurisdictions requires financial records for 5–7 years. GDPR's right to erasure has a "legal obligation" exception (Art. 17(3)(b)).

Resolution: model "deletion" as erasure of PII and operational data, not erasure of financial and legal records. Be explicit in your privacy policy about what gets retained and why. The deletion confirmation should say this, not hide it in a footer.

**3. Instant deletion vs. grace period**

Instant and irreversible deletion is dangerous: compromised admin credential, fat-finger, disgruntled employee with admin access. But a long grace period creates a different problem: the customer still has access to a "deleted" account, which confuses them and creates support load.

Resolution: a mandatory delay (commonly 14–30 days) with the account immediately suspended (no login, no API access, integrations revoked) but data not yet purged. Send confirmation email immediately, cancellation email at purge. Provide an undelete/cancel-deletion window. After the window, an async purge job runs — and must be monitored, because silent purge failures are a real failure mode.

**4. Who can request deletion**

In a team account: can any admin? Only the billing admin? Only the account owner? What if there are multiple owners? What if the requester's own account is under an active legal hold?

Resolution: gate deletion behind: (a) billing admin role specifically, (b) email confirmation to the registered billing contact (not just the session user — defense against session hijack), (c) optionally a waiting period before the deletion is even scheduled. Log the request and the identity of the requester in an append-only audit record.

**5. Third-party integrations**

OAuth tokens your org granted to Slack, Salesforce, etc. remain valid in those systems after you delete the org. Your system can revoke your side of the grant, but you cannot force the third party to purge cached data. API keys issued to the org that were used in customers' own pipelines will start returning 401s — causing downstream breakage that the org admin may not have anticipated.

Resolution: enumerate active integrations in the deletion confirmation step. Show the admin what will break. For OAuth: revoke all tokens during the suspension phase, not after the grace period — this is the one thing that should happen immediately. For API keys: invalidate on suspension. Provide a "what will be affected" summary before confirmation.

---

### The flow (at the right altitude)

```
Admin clicks "Delete account"
  → Show: what will be destroyed, what will be retained (legal), what integrations will break
  → Require: re-authentication (password or SSO) + email confirmation to billing contact
  → Immediate on confirmation:
       - Suspend org (no login, no API)
       - Revoke OAuth tokens and API keys
       - Cancel billing subscription (prorate if needed)
       - Send deletion-scheduled email with grace period end date
       - Log deletion request (append-only, retained per legal schedule)
  → Grace period (14–30 days):
       - Account suspended but data intact
       - Admin can cancel deletion via link in email
       - Members can export their own data
  → On grace period expiry:
       - Async purge job: delete PII, operational data, content
       - Retain: financial records (scoped to legal minimum), anonymized analytics, audit log metadata
       - Send deletion-complete confirmation
       - If purge fails: alert ops, do not silently skip
```

---

### Questions I'd ask before building

These are not rhetorical — each one changes the design:

1. **Do members have cross-org accounts on your platform?** If yes, org deletion must not touch member-level identity. If no (each account is single-org), the cascade decision is simpler.

2. **What jurisdictions are your customers in?** GDPR (EU), CCPA (California), PIPEDA (Canada), LGPD (Brazil) all have different erasure timelines and retention exceptions. Which do you need to comply with at launch?

3. **What is your current billing integration?** Stripe, Chargebee, Recurly all have different behaviors when you delete a customer record vs. cancel a subscription. You want to cancel the subscription, not delete the billing record — the invoices need to persist.

4. **Do you have any enterprise contracts with data retention requirements?** Some enterprise SLAs require you to retain data for 90 days after contract end. This overrides a 30-day grace period.

5. **What happens to content created by members that was shared with people outside the org?** (Shared links, exported reports, embedded content.) Does deletion break those? Should it?

6. **Is there a self-serve downgrade path?** Sometimes "delete my account" is really "I can't afford this anymore." Having a clear downgrade or pause path reduces deletion requests and is worth surfacing in the confirmation flow.

7. **Who in your company needs to be notified?** Sales (churn signal), success (is there a save opportunity?), finance (revenue impact), legal (if enterprise contract). This is operational, not just technical — the deletion event should emit to your internal tooling.

---

### What I'd build first vs. later

**Phase 1 (launch-blocking):**
- Suspension on request (immediate)
- OAuth/API key revocation (immediate)
- Billing cancellation
- Email confirmation + grace period mechanics
- Async purge with monitoring/alerting
- Audit log of the deletion request

**Phase 2 (compliance hardening):**
- Per-member data export before org deletion
- Explicit retention policy surfaced in UI
- Jurisdiction-aware retention schedules
- Legal hold flag that blocks deletion

**Phase 3 (operational polish):**
- Internal notification hooks (CRM, Slack alerts)
- "What will break" integration summary
- Admin dashboard showing pending deletions
- Reactivation flow (within grace period)

---

### The thing most teams get wrong

They build deletion as a single synchronous event and treat "deleted" as a binary state. In reality it's a multi-phase state machine (active → suspended → scheduled-for-purge → purged → legally-retained-stub), and different data has different state transitions. Getting the state model right before you write the first migration is far cheaper than retrofitting it after a compliance audit.

## END_TS
1780599345
