**Reflex first (step 1)**  
Without this process, my answer would be a generic GDPR/CCPA checklist: confirmation modal → soft-delete flag → 30-day grace period → hard delete with ON DELETE CASCADE. It would treat deletion as a single-row CRUD operation and likely miss the B2B landmines: dangling team ownership, orphaned third-party OAuth apps, broken billing continuity for remaining members, and audit-trail destruction.

**Triage (step 2)**  
- T1 multi-file / cross-system? The *topic* crosses auth, billing, teams, integrations, and compliance, but the *action requested* is advisory/design only.  
- T2 framing pressure? Moderate — “greenfield, no spec” creates pressure to be exhaustively prescriptive.  
- T3 expensive to roll back? Low — advice is reversible.  
→ **STANDARD** (frame + trace + zoom; advisory context keeps it from FULL, though I will include restricted inversion/alternatives because the business risk of getting this wrong is high).

---

### 3. Frame check (the center)

**A. What is the prompt asking me NOT to consider?**  
- It does not ask me to distinguish **“user self-exit”** (an individual leaving the platform or a team) from **“account/tenant closure”** (shutting down the whole organization). In B2B, “delete my account” is semantically ambiguous and building the wrong one is a classic greenfield error.  
- It does not specify a regulatory regime (GDPR vs. SOC 2 vs. HIPAA), which changes retention rules.  
- It does not mention pre-deletion obligations (data export/portability, billing finalization, ownership transfer).

**B. Actual problem or symptom?**  
The real problem is **safe, auditable offboarding** that severs access and liability for the departing party without breaking team continuity, financial record integrity, or integration security. The symptom-level framing is “we need a delete button.”

**C. What pressure is on me?**  
Pressure to deliver a “complete” architecture, which risks over-engineering (e.g., a generic deletion orchestrator) or under-engineering (treating a graph as a node).

**Reframe:** I will not design a single “delete user” endpoint. I will design a **decomposition policy** that handles both *User Exit* and *Tenant Closure* as separate lifecycle events coordinated across bounded contexts. If the product only needs one of these today, the policy matrix still prevents tomorrow’s accidental coupling.

---

### 4. Trace at the right altitude (zoom discipline)

Too broad: “Redesign the entire platform around an event mesh.”  
Too narrow: “Set `users.deleted_at = now()` and cascade in Postgres.”  
Right altitude: A **saga-style state machine** at the bounded-context boundary, with explicit tombstone rules per domain.

**System → Module → Policy line**

| Level | What must happen |
|-------|------------------|
| **System** | Deletion is a cross-aggregate *lifecycle contract*, not a single transaction. It must succeed partially and recoverably because third-party integrations will fail. |
| **Bounded Contexts** | Identity, Teams/Orgs, Billing/Subscriptions, Integrations (OAuth + API keys + webhooks), Audit/Compliance, Notifications. |
| **Policy lines (examples)** | Identity: scramble PII, revoke sessions, preserve non-PII primary key as tombstone. Billing: never delete invoices; cancel active subs; retain payment records. Teams: block sole-owner exit without transfer. Integrations: async token revocation; disable API keys immediately. Audit: append-only; replace FK with pseudonym. |

---

### 5. Reproduce-gate (grounded hypotheses)

I cannot run code (greenfield), but I ground the design in predicted failure modes:

1. **Orphaned billing:** *“If we hard-delete the `users` row and `invoices.purchased_by` FK references it with CASCADE, we lose financial records.”* Predicted failure: tax audit / SOC 2 finding.
2. **Zombie integrations:** *“If a user authorized a Slack OAuth app, deleting the user row without revoking tokens does not uninstall the app from the customer’s workspace.”* Predicted failure: security exposure; integration posts with an invisible “deleted” owner.
3. **Team lockout with continued charging:** *“If the sole owner deletes themselves and ownership auto-transfers to no one, billing settings become inaccessible but the subscription remains active.”* Predicted failure: support escalation, involuntary churn, chargebacks.

---

### 6. Inversion + alternatives (FULL-tier supplement)

**How would I make this worse?**  
Hard-delete the `users` record with database-level CASCADE into `audit_logs`, `invoices`, `projects`, and `integration_credentials`. Silent failure: it passes unit tests (the row is gone) and fails 90 days later during an audit or when a teammate tries to view project history.

**Alternatives:**

| Option | Downside | Silent failure mode |
|--------|----------|---------------------|
| **A. Do nothing / Support-driven only** | High support burden; compliance risk in regulated markets. | Users stop logging in but integrations and SSO access remain active; security drift. |
| **B. Immediate hard delete of everything** | Irreversible; violates financial/legal retention requirements. | Appears clean until auditor asks for Q1 invoice lineage or a teammate discovers all shared project data vanished. |
| **C. Pure anonymization (keep row, scrub PII)** | May fail GDPR “right to erasure” scrutiny if data is reconstructable. | SSO JIT re-provisions the same email and re-links to the anonymized row, re-surfacing prior associations. |

---

### 7. Design proposal (the delta)

**Core architecture: The Exit Matrix**

Do not build one endpoint. Build two semantically distinct flows controlled by a policy matrix.

| Flow | Actor | Trigger | Outcome |
|------|-------|---------|---------|
| **User Self-Exit**