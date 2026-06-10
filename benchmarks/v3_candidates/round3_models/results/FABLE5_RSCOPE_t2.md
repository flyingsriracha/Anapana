# FABLE5 × RSCOPE — Trial 2

## REFLEX
Without this process, my answer would be a single B2C-style flow: confirmation modal → soft-delete with 30-day grace → cancel the subscription → revoke integration tokens → cascade purge, plus a GDPR checklist bolted on.

## TIER
STANDARD. T2 fires: the feature name ("delete my account") presumes one deletion operation, and "greenfield, no existing spec" suppresses the pre-existing legal/contractual constraints that actually bound the design. T1 borderline: the subject is cross-system (billing, integrations, teams) but the act here is advisory text — the human decides. T3 no: nothing irreversible in proposing. 1–2 flags, borderline rounds up → STANDARD, not FULL (advisory blast radius; a weighty topic is not automatically FULL).

## ANSWER

### First decision: this is three features wearing one name

In a B2B product with team accounts, "delete my account" hides three distinct operations with different authority rules, different data treatments, and different legal triggers:

1. **Member deletion** — an individual leaves a workspace or wants their identity gone; the org keeps operating.
2. **Organization (tenant) deletion** — the whole account, billing, and every member's access go away.
3. **Erasure request (GDPR Art. 17 / CCPA)** — may arrive by email rather than UI; may come from an ex-user; may be routed through your customer rather than from the data subject directly.

Decide which you're shipping first, because each differs at the root. Most of the engineering is shared, though: all three sit on the same deletion pipeline. The button is an entry point; the pipeline is the product.

### The B2B-specific crux: ownership and authority

- **Controller vs. processor.** In most B2B arrangements your customer (the org) is the data controller for workspace content; you're the processor. An end user has strong rights over their *identity* (profile, email, credentials) but typically not over *work product the org owns* — docs, messages, tickets they authored in a shared workspace. So member deletion must split into:
  - *Remove membership* — access ends, org data untouched.
  - *Erase identity* — PII deleted; contributions remain but attribution is anonymized to a tombstone ("Former member"), preserving team history and referential integrity.

  Conflating these is the classic failure: cascade-deleting a departing member's rows destroys the team's shared content and breaks audit attribution. The prompt's own wording shows the trap — the possessive in "delete *my* account" collides with "team accounts."
- **Authority for org deletion.** Owner role only; fresh re-authentication (step-up if SSO); notify all admins; consider second-admin confirmation above a size threshold. Account takeover followed by "delete the company" is the nightmare — this flow is a high-value attack surface, and the grace period is the last line of defense.
- **Edge authority cases to define now:** sole owner has left the company (recovery path?); deletion with unpaid invoices; deletion mid-contract on an annual plan — the contract/DPA often already specifies what happens to data at termination, including a deletion SLA. "Greenfield" applies to your code, not to those obligations.

### Prerequisite deliverable: a data inventory with per-class disposition

You cannot design deletion until you can enumerate where account data lives. For each class, pick a disposition — delete, anonymize, or retain-with-documented-basis:

| Data class | Disposition | Why |
|---|---|---|
| Identity/PII (profile, email, credentials, avatar) | Hard delete / anonymize | Erasure rights |
| Org work product (docs, messages, comments) | Org deletion: purge after grace. Member deletion: retain, anonymize attribution | Org owns it |
| Billing/financial records (invoices, tax) | Retain for statutory period; excluded from erasure | Legal obligation overrides erasure — exact periods vary by jurisdiction; confirm with counsel |
| Audit/security logs | Retain time-boxed; pseudonymize user refs where feasible | Security/legitimate interest; SOC 2 expectations |
| Integration OAuth grants | Revoke **at the provider's** revocation endpoint, then delete locally; deregister webhooks | Deleting your token row does not kill the live grant |
| Data you pushed to third parties (CRM sync, analytics, support desk, email tools) | Propagate deletion via their APIs (e.g., billing-provider customer deletion, analytics user-deletion endpoints) | Sub-processor obligations |
| Derived stores: search indexes, caches, warehouse, ML artifacts | Delete/expire in the pipeline | They outlive the source row otherwise |
| Backups | Don't surgically edit; deletions age out with rotation (N days, documented); keep a tombstone list so any restore re-applies deletions | Standard, defensible if disclosed and time-bound |
| The deletion record itself | Retain minimal proof ("org X deleted on date Y per request Z") | You need compliance evidence that itself holds minimal PII |

If you can't produce this inventory today, that's task zero — and the strongest argument that milestone one is the pipeline plus a support runbook, not UI.

### The flow (org deletion as the flagship)

1. Request (owner-only) → fresh re-auth → **specific** consequence disclosure: what's deleted, what's retained and why, which integrations disconnect, export offered.
2. Typed confirmation (org name); notify all admins.
3. **Soft-delete + grace period** (14–30 days): logins blocked, data intact, support-recoverable; subscription canceled (decide immediate vs. period-end — refund policy interacts); export still obtainable.
4. **Hard purge** after grace: an async orchestrated job, never a synchronous request — third-party APIs fail, and partial deletion is the worst state: the account looks deleted, data persists, you carry breach exposure plus a false compliance claim. Per-store handlers, idempotent, retried, each emitting a completion record; a final verification pass; a deletion certificate if contracts require one.
5. Aftermath: minimal deletion record retained; backup-rotation clock disclosed.

Member deletion runs the same skeleton: revoke sessions/API keys/personal tokens, remove memberships, transfer org-owned resources (or tombstone), anonymize attribution, erase identity, adjust seats per proration rules.

Erasure requests may need no UI at all initially: a ticket-driven runbook driving the same pipeline, with the statutory clock (30 days under GDPR, extendable) tracked in your support tooling.

### Engineering notes

- **Don't implement deletion as DB CASCADE.** Invisible, unrecordable, untestable per-class, and it will eat shared rows. Explicit per-store handlers under an orchestrator.
- **Idempotency + ledger.** Every handler re-runnable; the orchestrator records per-system outcomes. That ledger is also your compliance evidence.
- **Coverage rot is the long-term failure mode.** Every new table, store, or integration silently escapes the purge. Add registration discipline: new data store ⇒ deletion handler required (checklist or CI lint against the schema).
- **Test end-to-end with a seeded synthetic org**, including sandboxed third-party calls, restore-from-backup re-deletion, and "deletion requested twice."

### Tensions to resolve explicitly, not silently

- **Erasure vs. retention**: right-to-erasure vs. tax/financial retention and audit-log integrity → resolve per data class with a documented legal basis, never one global rule.
- **"My" vs. "ours"**: the user's erasure right vs. the org's ownership of work product → the membership/identity split and tombstones.
- **Recoverability vs. the promise of deletion**: grace periods and backup rotation mean "deleted" isn't instant — defensible if time-boxed and disclosed, deceptive if hidden.
- **Self-serve vs. safety**: a frictionless delete button is an account-takeover kill shot; friction here (re-auth, typed confirmation, admin notification, grace) is a feature.
- **Ship-the-button vs. ship-the-pipeline**: if the driver is a compliance deadline or DPA commitment, pipeline + runbook discharges the obligation; UI is phase two.
- **Subscription timing**: immediate cancel (refund complexity) vs. end-of-period (you're holding data for a "deleted" account) — pick one and document it.

### Questions I'd ask before building

1. What's actually driving this — erasure-request volume, a specific enterprise DPA or deal commitment, marketplace policy, or off-boarding hygiene? Sets the deadline and phase one.
2. Which operation first: member deletion, org deletion, or erasure-request handling?
3. Which jurisdictions/regimes apply, and do existing contracts/DPAs already promise deletion SLAs at termination? Those documents are your real spec.
4. Per your DPA, do end users come to you directly for erasure, or are they routed to the customer as controller?
5. Can we enumerate every store and sub-processor holding account data today? If not, who owns producing that inventory?
6. What do finance/legal require us to retain (invoices, tax records), for how long, per jurisdiction?
7. Which integrations hold data we *pushed* (vs. merely tokens), and do their APIs support deletion?
8. Are enterprise customers on SSO/SCIM? Member deletion should align with SCIM deprovisioning semantics, not fight them.
9. Grace-period length and undo policy — what has support seen with accidental deletions?
10. Mid-cycle billing behavior: seat proration on member removal; refund vs. run-out on org deletion?
11. Does anything copy prod data outward today — warehouse, analytics, ML training, log shipping — and what's its retention?

### What I'd build first

Phase 1: data inventory + deletion orchestrator + per-store handlers + member remove/anonymize + support runbooks for org deletion and erasure (compliance is dischargeable immediately). Phase 2: self-serve org deletion UI with grace period and admin safeguards. Phase 3: erasure-request intake automation, deletion certificates, SCIM alignment.

One honest caveat: the statutory retention periods and the controller/processor allocation above are the standard pattern, not legal advice — they need counsel's confirmation against your actual contracts and jurisdictions before they harden into the spec.

## END_TS
1781056865
