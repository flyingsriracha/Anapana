# FABLE5 × RSCOPE t1 — "delete my account" design (B2B SaaS)

## REFLEX
Soft-delete with a 30-day grace period: confirmation modal, cancel the subscription, revoke integration tokens, GDPR-erase PII, cascade-clean the data — the standard checklist hung on a button.

## TIER
STANDARD — T1 yes (the design genuinely spans identity, billing, integrations, and the legal layer: cross-system), T2 yes (the feature's own name applies framing pressure — "my account" presupposes the individual-user object in a product where the deletable object is ambiguous), T3 no (pure advisory; the human acts, nothing to roll back on my side). 2 flags → STANDARD (frame + trace + grounding; no inversion section required).

## ANSWER

The first thing to settle is that in a team-based B2B product, "delete my account" is not one feature — it's at least three, and the worst public incidents in this space come from conflating them.

### Disambiguate the object before anything else

1. **A user deletes their identity** — login, profile, personal data. They leave; the team and its work stay.
2. **An admin removes a member** — employee offboarding. The org initiates it; the person may not even be reachable.
3. **An owner deletes the org/workspace** — the customer churns. Tenant data, the billing relationship, and every member's access go with it.

And a fourth that's invisible in the UI but dominates the engineering: **propagation** — backups, search indexes, analytics, the data warehouse, caches, and whatever you've already pushed to third parties.

Each has a different actor, different authority checks, different blast radius, and different legal basis. A single "Delete" button that cascades is how a departing employee destroys three years of a team's shared documents.

### The B2B legal spine changes the design more than people expect

For workspace content you're almost certainly the *processor*; your customer (the org) is the *controller*. An employee's GDPR/CCPA erasure request about work content legally routes through their employer — not through your self-serve UI. What your "delete my account" button properly controls is the slice you're controller of: their identity, profile, and marketing data. That narrows the self-serve feature substantially, and the narrowing is correct, not a dodge.

Equally important is what you must **not** delete: invoices and transaction records (tax retention, typically 6–10 years — confirm exact periods with counsel per jurisdiction), security audit logs you've committed to under SOC 2 or enterprise contracts, anything under legal hold. So the primitive is never "delete everything"; it's a per-category decision: hard-delete, anonymize, or retain-with-documented-reason.

Third: the org owns the work product. When a person is deleted, the default is **tombstoning** — their identity becomes "Deactivated user," their PII is erased, but their documents, comments, and audit-trail entries remain attributed to the anonymous placeholder. Deleting a person must never silently delete the team's history; content removal is a separate, org-controlled action.

### Design the sole-owner case first, not last

The most dangerous path: the requester is the org's only owner (and often its billing contact). Naive user-deletion either bricks the tenant — no owner, subscription still charging — or cascades into an org deletion nobody else consented to. Make the state unrepresentable: deletion of a sole owner is blocked behind a fork — *transfer ownership first*, or *explicitly convert this into org deletion*, which is a different, heavier flow. This is the edge case to design on day one, not handle in support tickets.

### The core mechanism: a state machine and an async pipeline, not an event

`active → deletion_requested → grace period (deactivated, recoverable) → purging → purged (tombstone)`

- **Request.** Re-authentication (step-up if available), a consequences screen specific to what will actually happen, type-to-confirm. Org deletion additionally: owner role required, a data export offered and acknowledged, an explicit list of what dies — data, members' access, integrations, the subscription.
- **Grace period (14–30 days).** Access dies immediately even though data doesn't: sessions revoked, API keys disabled, integration OAuth grants revoked at request time. The account is recoverable by logging back in. Notify at request, mid-window, and 48h before purge. The window is your defense against both compromised-account malicious deletion and genuine regret; keep a support path for the rare legitimate "purge me now."
- **Purge.** An asynchronous, idempotent, resumable job that walks a **deletion manifest**: an explicit registry of every store holding user or tenant data — primary DB, object storage, search, cache, analytics, warehouse, ML/derived artifacts — each entry declaring its policy (delete / anonymize / retain-with-reason / crypto-shred) and an owner. The manifest is the real deliverable: it's what keeps deletion honest as the schema grows. Enforce it — a new table or event stream that isn't registered should fail CI.
- **Backups.** Don't rewrite backups. Two honest options: (a) let them expire on rotation and publish the window ("fully removed within N days"), paired with a *deletion redo-log* that re-applies pending purges after any restore — otherwise a restore resurrects "deleted" users; or (b) **crypto-shredding** — per-user/per-tenant encryption keys, where deletion = key destruction. Greenfield is exactly when crypto-shredding is cheap; retrofitting it is brutal. Put it on the table now even if deferred.
- **Third parties, both directions.** Revoke what they hold on you (OAuth grants, webhooks). Then propagate erasure to processors you've pushed data into — email, CRM, analytics, support tooling; your payment processor will rightly refuse to erase transaction records. Keep a sub-processor register so "who do we have to tell?" is a lookup, not an investigation. You won't get synchronous confirmation from everyone — record requests and responses as evidence.
- **Completion.** Emit a **deletion certificate**: what was deleted, anonymized, retained, and on what basis, timestamped — the minimal record proving erasure, itself containing as little personal data as possible. This is what you hand auditors and DSR responses.

### Billing interlock (org deletion)

Deletion is not cancellation, but they must compose: cancel the subscription, settle or refund per policy, and issue the final invoice *before* purge — you can't invoice an entity you've erased. Billing records live outside the tenant's blast radius. Decide the unpaid-balance policy explicitly: erasure rights don't extinguish debts, but holding personal data hostage to collections is both illegal (in GDPR scope) and ugly — usually: deletion proceeds, the receivable survives in the financial system.

### The tensions to resolve (product decisions, not engineering ones)

1. **Erasure vs. retention.** Right-to-be-forgotten against tax, audit, and legal-hold duties. Resolved per data category in the manifest — never globally.
2. **The individual's rights vs. the org's ownership.** Their PII vs. the team's work product. Resolved by the tombstone boundary.
3. **Immediacy vs. safety.** Users want "gone now"; you want a window against compromise and regret. Resolved by instant access revocation + delayed data purge, with an expedited support path.
4. **Completeness vs. cost.** Synchronously scrubbing warehouse, backups, and derived data is enormously expensive. Resolved by crypto-shred or documented rotation windows — publish the real number rather than pretending instant.
5. **Friction vs. dark patterns.** Enough confirmation to prevent disasters, not a maze. Regulators and platform policies increasingly require deletion to be roughly as easy as signup; make the friction informative, not obstructive.

### What I'd ask before building

1. What's actually driving this — a compliance questionnaire, GDPR/CCPA exposure, a churned customer demanding destruction, a platform requirement? The driver decides which of the three deletions ships first.
2. What have we already signed? DPAs, retention clauses in enterprise contracts, the current sub-processor list. "Greenfield" applies to the code, not the obligations.
3. Which regimes apply — GDPR, CCPA/CPRA, anything sectoral (HIPAA, FINRA)? That sets the retention table and the SLA clock (GDPR: without undue delay, roughly a month).
4. Does a data inventory exist? If not, accept that building the deletion manifest *is* half the project, and budget for it.
5. Are SSO/SCIM in the picture? If the customer's IdP provisions users, a self-serve delete will fight tomorrow's directory sync, which recreates the user. Deprovisioning belongs to SCIM; erasure of our copies belongs to this feature — design them together.
6. Who can halt a purge (legal hold landing mid-grace-period), who can expedite one, and is that admin path itself audited?
7. Do we build analytics or train models on customer data? If yes, derived artifacts are in erasure scope and that materially shapes the architecture — decide now.
8. What does the backup story look like today — rotation period, restore runbook? That number is the honest "fully deleted within X days" you can publish.

### Order of build

1. Data inventory → deletion manifest with per-category policy. Foundation and audit artifact in one.
2. User deletion: tombstoning, sole-owner block, grace period. Highest frequency, bounded blast radius.
3. Org deletion: export, grace, billing interlock.
4. Propagation: integration revocation + erasure calls, warehouse, backup redo-log; deletion certificates.
5. Operability: a status view per deletion job, halt/expedite controls, evidence export for audits.

Ship the state machine with conservative policies; tightening a retention category later is a policy edit, not surgery. The two things genuinely expensive to retrofit — the manifest discipline and crypto-shredding — are exactly the ones to decide while it's greenfield.

Grounding note: the three predicted failure modes this design closes map one-to-one onto the givens in the brief — "team accounts" → a sole-owner or cascade deletion destroying shared work or bricking a tenant; "billing" → erasure colliding with legally mandated invoice retention (or retention used as an excuse to delete nothing); "third-party integrations" → deletion never propagating outward, so "deleted" data survives in processors and resurfaces from backups. Jurisdiction-specific retention periods above are hypotheses to verify with counsel, not findings.

## END_TS
1781056936
