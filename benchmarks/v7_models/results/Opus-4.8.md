# Working through SATORI-Lite

## Step 1 — Reflex first (freeze before reasoning)
Without this process, my answer would be: *"Here's a checklist — soft-delete the account, anchor the delete behind a confirmation modal and re-auth, cancel the billing subscription, revoke third-party integration tokens, run a 30-day retention window then hard-delete, export data on request for GDPR. Here's the schema and a state machine."* A competent generic feature spec, account-centric, treating "account" as a single user record. (Freezing this.)

## Step 2 — Triage
- T1 multi-file/cross-system? Yes, strongly — billing, integrations, team membership, data stores.
- T2 framing pressure? Yes, subtle. "delete my account" — "my" implies an individual + a single account; singular "account" hides the team/org structure. "Greenfield" invites producing a design rather than questioning the unit of deletion.
- T3 expensive to roll back? Advisory task — I propose, the human acts; but the subject matter is one of the most irreversible features a B2B SaaS ships.
Score 2 + irreversible subject → round UP → FULL.

## Step 3 — Frame check
A. Asked NOT to consider: who "my" is and what "account" means in B2B. There is no single account — there's an org/workspace and users (members). "Delete my account" is ambiguous between ≥4 ops: (1) member leaving a team (org survives); (2) admin deleting the whole org; (3) deleting a user identity spanning multiple orgs; (4) closing the billing account (which may differ from the workspace owner). The naive spec collapses all four — that collapse is the central error.
B. Actual problem: let customers leave cleanly and lawfully without destroying others' access, breaking billing, or stranding integrations. A single "delete" button creates harm: an owner nukes a 40-person workspace; the sole billing admin leaves and locks out the org; an integration token tied to the departing user breaks every teammate's sync.
C. Pressure: to deliver a confident-looking design. Disciplined move: lead with decomposition + the gating questions, not a schema. The reframe (several distinct deletions; org-vs-member must be decided first) is part of the answer.

## Step 4 — Trace at the right altitude
System: this is identity/tenancy lifecycle management; the right altitude is the tenancy model (org ↔ membership ↔ user), not a DELETE endpoint. Modules: tenancy/identity (last-owner invariant, SSO/SCIM-provisioned identities the IdP owns); billing (cancellation vs proration vs outstanding invoices; the org is the Stripe customer, not the user; tax records often must be RETAINED even after deletion); integrations (a token granted by a user but acting for the org — deleting the user revokes the org's integration; inbound API keys; webhooks to dead tenants); data stores & derivatives (primary DB, search, caches, blob storage, warehouse, logs, BACKUPS, and third-party processors). Line level: "cannot delete last owner," "cannot delete an org with an active paid subscription without explicit cancel," "a member's authored content is reassigned or tombstoned, not vanished." Fix at the right altitude = two distinct operations (member offboarding, org deletion) sharing a common deletion-execution substrate.

## Step 5 — Reproduce-gate (named failure modes of the naive single button)
1. Last-owner lockout → orphaned/unadministrable tenant. 2. Billing orphan (billing-owner ≠ org-survivor) → silent continued charges or revenue dispute. 3. Integration cascade (user-scoped but org-used token) → silent breakage for teammates. 4. Compliance contradiction: GDPR erasure vs tax retention vs legal hold. 5. Backup/sub-processor leak → data survives the "deletion," found in a later DSAR audit.

## Step 6 — Inversion + alternatives (FULL)
Worse: one red button, synchronous hard-delete everything on click, single confirm, no member/org distinction, no re-auth, no retention window, no fan-out, no audit log. Alts: (1) manual/support-ticket deletion — doesn't scale, GDPR liability, ad-hoc SQL misses warehouse/sub-processors. (2) Soft-delete only — fails right-to-erasure; data accumulates; "deleted" data stays queryable + in backups. (3, recommended) Two operations + soft-delete grace → async hard-erasure with sub-processor fan-out + retention carve-outs; silent failure to watch: a new store/sub-processor added later isn't wired into the fan-out → deletions silently stop being complete (needs a registry + test).

## Step 7 — Identity (delta)
Reflex: single account-centric checklist + schema. After: items survive but the frame inverts — first deliverable is "which deletion, member or org?", split into member-offboarding vs org-deletion, foregrounding B2B traps the reflex missed (last-owner, billing-customer ≠ user, user-granted-org-used tokens, retention law contradicting erasure law, backup/sub-processor fan-out), deletion as an async, auditable, recoverable-within-a-window pipeline.

---

# Final Design: B2B SaaS Account Deletion

## 0. Reframe (decide first — determines everything)
"Delete my account" is ≥2 features. **A. Member offboarding** (any member self / admin; one membership ends, org survives; seat decrement/proration; risk: orphaned content, lost integration). **B. Organization deletion** (owner/admin only; entire tenant ends; subscription cancellation; risk: mass data loss, billing finalization). Plus: is a "user" global or per-org? (if multi-org, deleting the user is a 3rd op, and leaving one org must NOT delete the identity). Who is the billing customer? (usually the org — deleting a user must never orphan the billing entity).

## 1. Invariants
1. Never delete the last owner/admin of a surviving org (force transfer or block). 2. Never silently destroy a paying org (require explicit cancel/ack of proration + final invoice). 3. A departing member's content is reassigned or tombstoned, never implicitly cascade-deleted. 4. Deletion is auditable (immutable log — itself a retention carve-out). 5. Erasure is eventually complete across all stores, governed by a data-store/sub-processor REGISTRY, not ad-hoc per-table code.

## 2. User-facing flow (same skeleton A & B)
Disambiguate intent (owner sees both "leave team" and "delete workspace"); pre-flight blockers shown before confirm (last-owner? active subscription? pending invoice? legal hold? sole integration grantor?); re-authenticate (step-up); explicit confirmation (type org name for B; state what's deleted vs retained-and-why + grace-period end); offer data export first (DSAR-friendly); email confirmation + recovery to owner(s).

## 3. Execution model (shared substrate): soft-delete → grace window → async hard-erasure
T0 soft delete (sync, fast, reversible): mark pending_deletion, IMMEDIATELY revoke sessions/API keys/integration tokens (security can't wait), stop billing accrual, hide from product. Grace window (14–30 days, configurable; map to DSAR SLA): guards accident/ATO/remorse; recovery restores. T+grace hard erasure (async, idempotent fan-out): iterate the data-store registry (DB, search, caches, blob, warehouse) AND issue erasure calls to every sub-processor (Stripe, Segment, email, support tool); each idempotent + logged. Backups: can't surgically edit most — document rolling backup expiry; restores re-apply pending deletions.

## 4. Billing teardown
Member offboarding: decrement seats; proration per policy; don't touch the org's payment instrument unless that member WAS the billing admin → force reassignment first (a blocker, not a cascade). Org deletion: cancel at period end or immediately per policy; finalize outstanding invoices; RETAIN invoice/tax records for the legally required period (survive erasure as a documented carve-out); remove stored payment methods.

## 5. Integrations teardown
Revoke outbound OAuth tokens (call the provider's revoke endpoint, don't just drop the row); revoke inbound API keys/PATs; tear down webhooks to the dead tenant; B2B trap — for an integration a MEMBER authorized but the ORG relies on, transfer the grant (re-auth as another admin) BEFORE removing that member, else offboarding silently breaks the team's sync.

## 6. Compliance (resolve the contradiction explicitly)
Erasure (GDPR 17/CCPA) pushes delete-on-request-within-SLA; retention law + legal holds push preserve-specific-records. Resolution: erase by default, retain by exception — explicit list of carve-outs (invoices, audit log, fraud/abuse, legal hold) with the legal basis for each. A legal hold OVERRIDES deletion (block/quarantine, don't erase). You're the controller; sub-processors are processors — obligation flows to them via the registry-driven fan-out. For team accounts, clarify in the DPA who can request deletion of whose data.

## 7. Build first (sequencing)
1. Decide the model (member/org/global user; billing customer). 2. Member offboarding + the last-owner/last-billing-admin/last-integration-grantor blockers + token revocation. 3. Soft-delete + grace + recovery substrate. 4. Async erasure job + data-store/sub-processor registry (start it now even if small — it rots silently). 5. Org deletion on top. 6. Self-serve export (also satisfies DSAR access).

## Open questions before building
1. Can one identity belong to multiple orgs? 2. Is the org or a user the billing customer of record? 3. Contractual/legal DSAR deadline (sets grace ceiling)? 4. Data-residency/industry rules (HIPAA, SOC 2, regional)? 5. Are some users SSO/SCIM-provisioned (IdP owns lifecycle — deprovision, not delete)? 6. Default for a departing member's content: reassign or tombstone?

Bottom line: don't build a button — build two lifecycle operations over one shared substrate (re-auth → soft-delete → grace → async registry-driven erasure with sub-processor fan-out), governed by B2B invariants, erase-by-default/retain-by-exception. Decide tenancy + billing-ownership first.
