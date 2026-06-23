## SATORI-Lite Working-Through

### Step 1 — Reflex
Without this process: a bullet checklist — data deletion, grace period, confirmation email, cascade to billing, GDPR + cascade deletes, schema. Competent but flat. Frozen.

### Step 2 — Triage
T1 cross-system? Domain is inherently cross-system (accounts, billing, integrations, data stores) → fires. T2 framing pressure? "Greenfield, no spec" is a scope-setter, not pressure → no. T3 expensive to roll back? Advisory — I propose, human acts → no. Score 1 → FAST, but the domain touches irreversible actions → treat as STANDARD (frame + trace of failure modes).

### Step 3 — Frame check
A. Asked NOT to consider: "delete my account" frames a consumer mental model (one person, one account). In B2B team accounts the actor is an owner/admin, and the account holds other members, shared data, active billing. Also not asked: the vendor side (what must be retained — legal holds, audit, financial records), the non-initiating members, downstream integration partners. B. Actual problem: a B2B customer (org, not individual) wants to fully exit — three actors (owner who initiates, billing that must settle, members who lose access). It's org-level offboarding, not personal data erasure alone. GDPR Art.17 erasure vs financial-record retention can conflict → often delete personal data, retain legally-required records, anonymize the rest. C. Pressure: only the pull toward comprehensiveness; resist over-engineering, stay at the right altitude (what must the team decide; what are the real failure modes). Reframe: widen from individual self-deletion to org-level offboarding; state it, don't stop.

### Step 4 — Trace
Modules to coordinate: identity/auth (who may trigger — owner, not any member); team membership (others lose access, notified, authored data); billing/subscription (cancel/resolve, unpaid invoices, proration, refunds); third-party integrations (OAuth grants, webhooks, API keys, data the integration holds); data stores (UGC, logs, config — delete vs anonymize vs retain); legal/compliance (retention, audit, GDPR/CCPA); notification/async pipeline. Named failure modes: non-owner triggers; co-owners disagree; members lose access with no warning mid-work; subscription cancelled but credit not refunded, or survives and keeps charging; third-party app keeps a live OAuth token calling deleted data; webhook keeps firing to a dead account; row deletion misses soft-delete flags; backups retain PII past window; anonymization reversible via quasi-identifiers; financial audit logs deleted → SOC 2 gap; or all PII retained under "legal hold" forever; user expects immediate deletion but gets a 30-day window unexplained; can't re-register same email because account is "pending deletion." Altitude = system-design level: policies, state machine, actor permissions — not SQL cascades, not vague "consider compliance."

### Step 5 — Reproduce-gate
Design/advisory, no codebase → grounded in named failure modes above, not code. No hypotheses stated as findings.

---

## Final Design: "Delete My Account" for B2B SaaS

### Core reframe
Not "delete my user profile" — org-level offboarding: cancelling an org's relationship with the product, which includes personal-data erasure as one obligation. An offboarding workflow with an identity checkpoint at the front, not a CRUD delete.

### Actor model
Only the org owner (or a designated billing admin) initiates deletion — not member-level. Other members have a stake; deletion is irreversible/costly; a single disgruntled admin shouldn't destroy an org. Decide: single vs shared ownership; unanimity vs one; add a re-auth gate (password + MFA) immediately before the flow — don't rely on the session.

### State machine
ACTIVE → DELETION_REQUESTED → GRACE_PERIOD → SCHEDULED_DELETION → DELETED (soft) → PURGED (hard). Requested: after re-auth + confirmation; notify ALL members immediately; cancel subscription now or at period end (documented policy, don't silently keep charging); begin token revocation. Grace (default 30d): org frozen (read/export only or full lock — decide + communicate); owner can cancel (reactivation); clear "permanently deleted on [date]" messaging. Scheduled: background, durable, idempotent, restartable job — not in a web request. Deleted (soft): member access revoked; personal data deleted/anonymized per policy; legally-required records (invoices, audit) tombstoned (retained, inaccessible to customer, ~7y financial); release primary email unless legal hold. Purged (hard): after retention window, purge tombstoned records — don't omit this; it's required for a credible erasure process.

### Billing (where most get it wrong)
Active subscription: cancel — immediate (prorated refund) or at period end (no refund); documented; build into Requested step. Unpaid invoices: block deletion until settled, or allow + write off/pursue via AR. Credits/prepaid: refund or forfeit (ToS + surfaced in flow). Annual plans mid-term: business decision, engineering implements. Billing provider: cancel the Stripe subscription + scheduled invoices; decide whether to detach payment methods; don't retain payment data longer than necessary.

### Team members
Notice to all at Requested time with the end date; export own data during grace; post-deletion login gives a clear "this org has been deleted" message, not a 404; member user records are NOT deleted (may belong to other orgs) — only their membership + org-scoped data.

### Third-party integrations (most underdesigned)
Revoke OAuth grants your product holds (call each provider's revoke endpoint, not just delete the row); revoke API keys/OAuth tokens external apps use for this org; cancel outbound webhooks (else fire to dead/recycled endpoints — wasted compute + leak risk); notify data-sharing partners per contract; be explicit that data exported to third parties (e.g. Salesforce) is outside your control.

### Data handling (decision tree)
Personal data: delete/anonymize at DELETED (irreversible token, watch quasi-identifiers). Org content: delete subject to legal hold. Financial records: tombstone for retention period. Audit logs: retain for SOC 2 period. Backups (the hard one): contain PII for weeks — state backup retention window; purge backups or disclose natural-expiry removal (GDPR 17(3) allows a documented delay). Analytics: aggregate may be retained; individual-level deleted/anonymized.

### Legal/compliance
GDPR Art.17 (the deletion flow is the mechanism; 30d window OK if disclosed); CCPA similar; retention exceptions under 17(3) (legal obligation, legal claims) — document the basis for financial-record retention; legal holds BLOCK SCHEDULED_DELETION and route to legal; check DPA obligations; offer data export (Art.20 portability) before deletion.

### UX
Make consequence legible (plain "permanent" + date); data export path before point of no return; friction confirmation (type org name); grace emails at T+0, +7d, −3d with one-click reactivation; final confirmation email; allow re-signup with the same email (it belongs to the person).

### Engineering notes (right altitude)
Idempotent durable queue-based job; checkpoint each step; soft-delete before hard-delete (recovery path); test the full pipeline in staging with a real test org incl. integration revocation + billing cancel + notifications; monitor stuck jobs / failed revocations / billing-cancel exceptions; audit-log the deletion pipeline itself (immutable).

### Decide before coding (business, not engineering)
Immediate vs end-of-period cancel; refund/proration; outstanding balances; grace length; read-only vs full lock; single vs multi-owner approvals; offer pause/downgrade before delete (churn); export optional vs mandatory; what's retained, how long, legal basis; legal-hold owner/process.

### Step 7 — Identity (delta)
Reflex was actor-blind (single-user), data-centric (rows/tables), skipped the state machine. Worked design reframed to org-level offboarding, centered the actor-permission problem first, built a concrete state machine with named failure modes per transition, separated legal retention from data deletion (the commonly confused distinction), and surfaced integration revocation (absent from the reflex). Billing expanded from "cascade" to a 5-state decision tree. Reflex would have produced a plausible but operationally incomplete spec; this surfaces the decisions the team must make before engineering starts.
