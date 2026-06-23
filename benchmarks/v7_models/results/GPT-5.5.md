Without this process, my answer would be a generic GDPR-style checklist for account deletion with a self-serve button and background job.

## Triage

**Tier: FULL.**  
This is cross-system, affects shared team/account resources, billing, compliance, identity, and third-party integrations. Deletion is also hard to undo if implemented incorrectly.

## Frame check

The dangerous ambiguity is the phrase **“delete my account.”** In a B2B SaaS, that can mean several different things:

1. Delete my individual user login.
2. Remove me from a team/workspace.
3. Delete the whole company/team account.
4. Cancel billing/subscription.
5. Delete company-owned data I created.
6. Revoke third-party integrations.
7. Exercise a privacy/erasure request.

Those should not be treated as one action.

The real problem is not “add a delete button.”  
The real problem is to design a **safe account lifecycle and data-erasure system** that distinguishes personal identity, company-owned workspace data, billing records, audit/security records, and externally shared data.

---

# Recommended design

## 1. Define deletion types explicitly

I would model at least four separate operations.

### A. Delete personal user account

For an individual user who wants to delete their login/profile.

Effects:

- User can no longer sign in.
- Personal profile data is deleted or anonymized.
- OAuth tokens, sessions, API keys, MFA devices, and personal access tokens are revoked.
- User is removed from workspaces where permitted.
- Auth identity is deleted or tombstoned.
- Authored company-owned content may remain, attributed to `Deleted User`.

This should be available to most users, but with guardrails.

Example label:

> Delete my user account

Not:

> Delete account

---

### B. Leave or remove from workspace/team

For users who only want to leave a company/team.

Effects:

- Membership removed.
- Seat may be freed.
- User loses access to that workspace.
- Workspace data remains.
- Billing may update depending on plan.

Example label:

> Leave workspace  
> Remove member

---

### C. Delete organization/workspace/company account

For owners/admins deleting the entire B2B account.

Effects:

- Cancel subscription or mark for cancellation.
- Schedule deletion of workspace data.
- Revoke integrations.
- Disable users’ access to that workspace.
- Retain legally required billing, tax, security, fraud, and audit records.
- Delete/anonymize customer content according to retention policy.

This should require elevated authorization.

Example label:

> Delete workspace and company data

---

### D. Cancel subscription

Billing cancellation is related but not identical to deletion.

Effects:

- Stop renewal.
- Retain workspace through end of paid period, grace period, or immediate cancellation depending on policy.
- Keep invoices/payment records as legally required.
- Does not necessarily delete user or workspace data.

Example label:

> Cancel subscription

---

## 2. Create a data classification matrix

Before implementation, inventory every category of data and decide what happens to it.

Example matrix:

| Data category | Delete? | Anonymize? | Retain? | Notes |
|---|---:|---:|---:|---|
| User name, avatar, bio | Yes | Optional | No | Personal profile data |
| Email address | Usually yes | Maybe hash/tombstone | Sometimes | Need to prevent account resurrection conflicts |
| Password hash | Yes | No | No | Delete with auth identity |
| MFA devices | Yes | No | No | Revoke immediately |
| Sessions | Yes | No | No | Revoke immediately |
| API keys / PATs | Yes | No | No | Revoke immediately |
| Workspace membership | Yes | No | Maybe tombstone | Needed for historical audit |
| Authored company content | Usually no for user deletion | Attribute to Deleted User | Yes | Company-owned in B2B |
| Comments/messages | Depends | Redact author PII | Maybe | Product/legal decision |
| Audit logs | Usually retain | Pseudonymize where possible | Yes | Security/compliance |
| Billing customer record | No immediate delete | Minimize | Yes | Tax/accounting/legal requirements |
| Invoices | Retain | No | Yes | Legal/tax retention |
| Payment method tokens | Delete/detach | No | Maybe processor retains | Coordinate with Stripe/etc. |
| Integration tokens | Yes | No | No | Revoke with third parties |
| Webhook configs | Delete for org deletion | No | No | Not for user deletion unless personal |
| Support tickets | Depends | Redact requester PII | Maybe | Retention policy needed |
| Product analytics | Aggregate | Anonymize | Maybe | Avoid re-identification |
| Backups | Eventually expire | No direct mutation usually | Temporary | Document backup retention |
| Legal holds | No | No | Yes | Must override deletion |

This matrix is the core spec. Without it, engineers will make inconsistent deletion choices service by service.

---

## 3. Permission and eligibility rules

### Personal user deletion

Allow a user to delete their personal account unless blocked by one of these cases:

- They are the sole owner/admin of an active workspace.
- Their account is managed by enterprise SSO/SCIM.
- There is an active legal hold or fraud/security investigation.
- They have unpaid invoices or contractual obligations attached personally, if applicable.
- They own personal integration connections required by an active workspace.

For sole owner/admin cases, require one of:

- Transfer ownership.
- Delete the workspace.
- Invite another owner.
- Contact support for enterprise-managed accounts.

### Workspace deletion

Require:

- Owner/admin role.
- Recent re-authentication.
- MFA challenge if enabled.
- Explicit confirmation of workspace name.
- Clear warning about consequences.
- Optional second-admin approval for enterprise/high-value accounts.
- Billing state check.
- Legal hold check.
- Integration impact preview.

For large B2B customers, I would seriously consider making workspace deletion a **request flow** rather than instant execution.

---

## 4. UX flow

## Personal user deletion flow

1. User visits account settings.
2. Page explains alternatives:
   - Leave workspace.
   - Delete personal account.
   - Delete workspace, if owner.
   - Cancel subscription, if billing admin.
3. User chooses “Delete my user account.”
4. System displays impact:
   - You will lose access to X workspaces.
   - Your profile will be removed.
   - Company-owned content may remain.
   - Your name may appear as “Deleted User.”
   - Billing/admin records may be retained where required.
5. Require re-authentication.
6. Optional cooling-off period, e.g. 7 or 14 days.
7. Immediately revoke active sessions or schedule deletion depending on policy.
8. Send confirmation email.
9. Provide request status.

## Workspace deletion flow

1. Owner/admin selects “Delete workspace.”
2. Show impact summary:
   - Members affected.
   - Subscription/billing impact.
   - Integrations to revoke.
   - Data categories deleted/retained.
   - Retention period.
3. Require typed confirmation, e.g. workspace slug/name.
4. Require re-authentication and MFA.
5. Optional second admin approval for enterprise plans.
6. Place workspace into `deletion_scheduled`.
7. Disable new writes or limit access.
8. Run async deletion workflow.
9. Send completion notice and export/delete certificate if appropriate.

---

## 5. State model

Avoid one boolean like `deleted = true`.

Use explicit lifecycle states.

For users:

```text
active
deactivation_requested
deletion_scheduled
deleting
deleted
deletion_failed
retained_due_to_hold
```

For workspaces:

```text
active
cancelled
suspended
deletion_requested
deletion_scheduled
deleting
deleted
deletion_failed
retained_due_to_hold
```

For deletion jobs:

```text
requested
approved
scheduled
in_progress
partial_failure
completed
blocked
cancelled
```

The deletion operation should be idempotent and resumable.

---

## 6. Architecture approach

Use an asynchronous deletion orchestration system.

### Main components

1. **Deletion request API**
   - Creates deletion request.
   - Validates actor permissions.
   - Performs eligibility checks.
   - Records request metadata.

2. **Policy engine**
   - Determines what should be deleted, anonymized, retained, or blocked.
   - Applies jurisdiction, plan, legal hold, and enterprise contract rules.

3. **Deletion orchestrator**
   - Executes deletion across services.
   - Maintains status.
   - Retries failures.
   - Emits audit events.
   - Supports idempotency.

4. **Per-service deleters**
   - Identity service.
   - Workspace service.
   - Billing service.
   - Integrations service.
   - Notifications service.
   - Files/storage service.
   - Analytics pipeline.
   - Search/indexing service.
   - Support/CRM sync.
   - Data warehouse.

5. **Tombstone records**
   - Preserve minimal non-PII or pseudonymous identifiers to prevent broken references.
   - Example: `user_123` becomes `deleted_user_abc`.

6. **Audit trail**
   - Record who requested deletion, when, from where, and what was done.
   - Do not put unnecessary PII in the deletion audit trail.

---

## 7. Integration handling

For third-party integrations, deletion must do more than remove local rows.

Consider:

- Revoke OAuth tokens.
- Delete access tokens and refresh tokens.
- Remove webhooks.
- Notify external systems if required.
- Stop background sync jobs.
- Delete cached third-party data.
- Remove integration-created credentials.
- Handle third-party retention policies.
- Record failures and retry.

Example risks:

- User deleted locally but their Google/Slack/Salesforce token still works.
- Workspace deleted but webhook endpoint continues receiving events.
- Integration cache remains searchable.
- External provider cannot delete data immediately, but you fail to disclose this.

---

## 8. Billing handling

Billing must be separate from data deletion.

For Stripe-like billing:

- Cancel subscriptions according to plan policy.
- Detach payment methods where allowed.
- Retain invoices and transaction records as legally required.
- Retain customer ID mappings if needed for tax, chargebacks, disputes, or accounting.
- Avoid deleting records required for revenue recognition.
- Ensure user deletion does not accidentally delete company billing ownership.
- If billing contact deletes their user account, require reassignment.

Important distinction:

> Deleting a user should not necessarily cancel the company subscription.  
> Deleting a workspace may cancel or schedule cancellation of the subscription.

---

## 9. Legal, compliance, and retention

You need explicit policy decisions before engineering hard-delete behavior.

Consider:

- GDPR/UK GDPR erasure rights.
- CCPA/CPRA deletion rights.
- SOC 2 auditability.
- HIPAA/BAA if applicable.
- DPA commitments.
- Contractual enterprise retention promises.
- Tax/accounting retention.
- Security logs retention.
- Fraud prevention.
- Litigation/legal holds.
- Backup retention.
- Data residency.

This should become an internal retention schedule.

Example:

```text
Customer content: deleted within 30 days after workspace deletion.
Backups: expire within 90 days.
Invoices: retained for 7 years.
Security audit logs: retained for 1 year, with user PII minimized.
Product analytics: anonymized within 30 days.
Integration tokens: revoked immediately.
```

Do not promise “immediate deletion from all systems” unless you can actually do it.

---

## 10. Backups and derived systems

Backups are commonly mishandled.

Policy should state:

- Deleted data may persist in encrypted backups until backup expiry.
- Backups are not restored except for disaster recovery.
- If restored, deletion jobs must be replayed.
- Backup retention period must be documented.
- Derived systems/search indexes/caches/data warehouse must be handled explicitly.

Also include:

- Search indexes.
- CDN caches.
- Object storage.
- Data warehouse.
- BI tools.
- ML/analytics datasets.
- Logs.
- Error monitoring tools.
- Session replay tools.
- Support tooling.
- CRM/marketing systems.

---

## 11. Security controls

Deletion is high-risk.

Add:

- Recent re-authentication.
- MFA challenge.
- CSRF protection.
- Rate limiting.
- Strong authorization checks.
- Admin action audit logs.
- Anti-clickjacking protections for destructive flows.
- Email notification to user/admins.
- Optional delay/cooling-off period.
- Anomaly detection for mass deletion.
- Support escalation for suspicious requests.

For workspace deletion, notify all owners/admins.

---

## 12. Observability and operations

Deletion jobs need operational visibility.

Track:

- Number of deletion requests.
- Requests blocked by policy.
- Jobs in progress.
- Jobs failed by service.
- Age of oldest pending deletion.
- SLA breach count.
- Integration revocation failures.
- Data warehouse deletion lag.
- Backup expiry lag.
- Manual intervention count.

Provide internal tooling to inspect a deletion request without exposing unnecessary PII.

---

## 13. API design

Expose deletion as a resource, not a synchronous action.

Example endpoints:

```http
POST /v1/me/deletion-requests
GET /v1/me/deletion-requests/{id}

POST /v1/workspaces/{workspace_id}/deletion-requests
GET /v1/workspaces/{workspace_id}/deletion-requests/{id}
POST /v1/workspaces/{workspace_id}/deletion-requests/{id}/cancel
```

Response example:

```json
{
  "id": "delreq_123",
  "target_type": "workspace",
  "target_id": "ws_456",
  "status": "scheduled",
  "requested_by": "user_789",
  "scheduled_for": "2026-07-01T00:00:00Z",
  "retention_summary": {
    "customer_content": "delete",
    "billing_records": "retain_legal",
    "audit_logs": "retain_minimized",
    "backups": "expire_after_retention"
  }
}
```

Use idempotency keys for creation.

---

## 14. Product copy matters

Bad copy creates legal and trust risk.

Avoid:

> Delete account

Prefer precise options:

> Delete my user account  
> Leave this workspace  
> Delete workspace and company data  
> Cancel subscription

Example warning for personal deletion:

> This deletes your personal user account and removes your access to workspaces. Content owned by your organization may remain and may be attributed to “Deleted User.” Some records, such as invoices, security logs, and audit records, may be retained where legally required.

Example warning for workspace deletion:

> This schedules deletion of workspace data for Acme Inc. Integrations will be disconnected, users will lose access, and the subscription may be cancelled. Billing records, security logs, and legally required records may be retained according to our retention policy.

---

# Implementation plan

## Phase 1: Policy and inventory

Deliverables:

- Data inventory.
- Retention matrix.
- Deletion semantics.
- Legal/compliance review.
- Product copy.
- Support runbook.
- Enterprise exceptions.

Do not start implementation before this is done.

---

## Phase 2: Minimal safe deletion platform

Build:

- Deletion request model.
- Eligibility checks.
- Re-auth/MFA.
- Audit logging.
- Async job orchestration.
- Identity/session/token revocation.
- User anonymization.
- Workspace membership removal.
- Admin notifications.

This supports personal user deletion first.

---

## Phase 3: Workspace deletion

Add:

- Workspace deletion request flow.
- Billing integration.
- Integration revocation.
- Storage/object deletion.
- Search/cache invalidation.
- Data warehouse handling.
- Export-before-delete option.
- Grace period/cancel deletion.
- Completion notification.

---

## Phase 4: Compliance hardening

Add:

- SLA reporting.
- Data subject request tracking.
- Legal hold integration.
- Backup restoration replay process.
- Enterprise admin controls.
- SCIM/SSO handling.
- Evidence package for audits.

---

# Reproduce-gate / grounded risk prediction

The prompt says:

> “B2B SaaS (team accounts, billing, third-party integrations)”

and asks for:

> “‘delete my account’ feature”

Predicted failure if treated literally: the team will likely implement a user-level delete button that either under-deletes personal data or over-deletes company-owned resources. The highest-risk failures are orphaned billing records, still-active integration credentials, broken workspace ownership, retained PII in derived systems, and accidental deletion of shared company data.

No codebase or existing spec is available, so this is a design-risk hypothesis, not a code finding.

---

# Inversion: how to make this worse

## Bad path 1: One synchronous hard-delete button

“Delete account” immediately cascades through database tables.

Downside:

- Easy to delete company-owned data accidentally.

Silent failure mode:

- Derived systems, billing providers, search indexes, analytics, logs, and integrations still retain data even though the UI says deletion succeeded.

---

## Bad path 2: Only soft-delete the user row

Set `users.deleted_at` and hide them from the UI.

Downside:

- Fast to ship but privacy-incomplete.

Silent failure mode:

- Tokens, sessions, integration credentials, analytics identifiers, support tickets, and billing contacts remain active or identifiable.

---

## Bad path 3: Let any admin delete the whole workspace instantly

Treat workspace deletion as just another admin setting.

Downside:

- Malicious or compromised admin can destroy business-critical data.

Silent failure mode:

- Organization cannot recover, support has no clear audit trail, and billing/subscription state becomes inconsistent.

---

## Bad path 4: Promise total deletion everywhere immediately

Marketing/legal copy says “all your data is permanently deleted immediately.”

Downside:

- Technically false for backups, invoices, logs, and third-party processors.

Silent failure mode:

- Compliance audit discovers retained data that contradicts the promise.

---

# Alternatives

## Alternative 1: Support-mediated deletion only

Users submit deletion requests to support.

Pros:

- Safer initially.
- Handles edge cases manually.
- Good for enterprise customers.

Downside:

- Slow and operationally expensive.

Silent failure mode:

- Support handles requests inconsistently without a rigorous retention matrix.

---

## Alternative 2: Self-serve personal deletion, support-mediated workspace deletion

This is my recommended starting point for many B2B SaaS products.

Pros:

- Users can exercise personal account deletion.
- Company-wide deletion remains controlled.
- Lower blast radius.

Downside:

- Less convenient for small teams that expect self-serve workspace deletion.

Silent failure mode:

- Support backlog causes deletion SLA violations.

---

## Alternative 3: Full self-serve deletion for both users and workspaces

Pros:

- Best UX.
- Scales well.
- Reduces support load.

Downside:

- Requires stronger controls, observability, policy maturity, and recovery planning.

Silent failure mode:

- A workspace deletion job partially fails, but the UI reports success.

---

## Alternative 4: Do nothing for now

Pros:

- No immediate engineering cost.

Downside:

- Bad user trust, likely compliance risk, support burden.

Silent failure mode:

- Ad hoc manual deletion accumulates inconsistent data handling across systems.

---

# Recommended approach

I would launch this in stages:

1. **Define deletion semantics first.**
   - Separate user deletion, workspace deletion, membership removal, and billing cancellation.

2. **Create the data retention matrix.**
   - Decide delete/anonymize/retain for each data category.

3. **Build a deletion request/orchestration system.**
   - Async, idempotent, auditable, resumable.

4. **Ship self-serve personal user deletion first.**
   - With safeguards for sole owners, SSO/SCIM users, billing contacts, and legal holds.

5. **Ship workspace deletion second.**
   - Owner-only, re-authenticated, delayed, auditable, with billing and integration handling.

6. **Do not represent deletion as instantaneous total erasure.**
   - Be precise about retained records, backup expiry, and third-party processors.

Final product model:

- **Delete my user account**: self-serve, guarded.
- **Leave workspace**: self-serve.
- **Cancel subscription**: billing-admin action.
- **Delete workspace/company data**: owner/admin action, likely delayed or request-based.
- **Privacy deletion request**: trackable request with policy-based execution.

## Identity delta

Initial reflex answer would have been: generic GDPR checklist plus a delete button and background job.

Actual proposal: treat “delete my account” as a set of distinct B2B lifecycle operations, backed by a data-retention matrix, permission model, async deletion orchestration, billing/integration handling, legal retention policy, observability, and staged rollout.