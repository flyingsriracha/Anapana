## REFLEX
Hard-delete with grace period, simple webhook, prorated refunds.

## TIER
STANDARD (T1: multi-system ✓, T2: no, T3: irreversible ✓)

## FRAME CHECK

**A.** Prompt excludes legacy data baggage and regulatory theatre.

**B.** Actual problem: deletion is irreversible + touches auth/billing/integrations simultaneously — not a symptom.

**C.** Implicit pressure: B2B SaaS must ship this to be competitive; no explicit deadline.

## MEDITATION_TRACE

**Step 1:** Design safe, auditable deletion for B2B SaaS handling auth, billing, integrations, team accounts, avoiding silent failures.

**Step 2 (end-to-end trace):** Auth must revoke all tokens/sessions immediately (blocking). Billing must cancel subscription and handle refunds without race conditions (queued). Integrations must call third-party DELETE webhooks idempotently. Team roles must not orphan orgs. Data retention must satisfy compliance (7yr audit log, soft-deleted records). Email notification must reach all stakeholders (user, org owner, integrations).

**Step 3 (first manifestation + origin):** Manifestation: user deletes account, receives deletion-complete email, then gets charged $99 next month. Origin: billing system wasn't coordinated in trigger; subscription cancellation was queued but failed silently.

## IDENTITY CHECKPOINT

Baseline reflex was "soft-delete with grace period"; trace reveals grace periods create billing ambiguity and webhook storms. Shifting to hard-delete immediately (with soft-delete only for billing records during settlement window) is a material change.

## ANSWER

### Delete My Account: B2B SaaS Design

**Core architecture:**

1. **Deletion ceremony (enqueued, not synchronous)**
   - Authenticate user (MFA if set).
   - Create deletion record.
   - Revoke all tokens/sessions immediately (blocking — no async).
   - Mark subscription "scheduled for cancellation."
   - Queue async workers: integrations, billing, data archival, notifications.
   - Return read-only status URL to user.

2. **Billing strategy**
   - Hard-delete user data immediately; soft-delete billing records until settlement window closes (~45 days).
   - Rationale: compliance (GDPR data minimization) + operational safety (no mid-flight payment chaos).
   - Define refund policy upfront (full, prorated, none, or credit). Initiate refund in deletion job.
   - Cancel subscription immediately; no grace period.

3. **Third-party integrations (webhook-based)**
   - Send DELETE webhook to all connected apps with user ID + timestamp.
   - Idempotent: caller can retry without side effects.
   - Unreachable = log, retry asynchronously, don't block.
   - Warn users: some third parties (Slack, GitHub) may retain unrevoked data.

4. **Team accounts**
   - If member: delete role binding; others unaffected.
   - If sole owner: require member promotion or explicit org deletion (prevent orphans).

5. **Audit trail**
   - Soft-delete account record (keep for 7 years, compliance).
   - Log: who, when, what deleted, what retained, any job failures.
   - Immutable, write-once.

6. **Silent failure mitigation**
   - **Risk**: Billing thinks account exists; user doesn't. Query billing after job completes; assert subscription cancelled.
   - **Risk**: User re-signs with same email. Soft-delete email for 30 days (hold it), or require re-verification.
   - Emit deletion success metrics.

### Questions to ask before building

1. Refund policy (full/prorated/none/credit)?
2. Grace period for undo (7 days or instant)?
3. Billing settlement window (instant or batched)?
4. Data retention: what's legally required (invoices) vs. deletable (logs)?
5. Team deletion: cascade to all members or just remove role?
6. Integration comms: webhook only or email too?
7. Support override: can support staff force-delete, or user consent only?
8. Audit retention: how many years, who can access?

### Proposed architecture

- **Deletion Service** (owns ceremony, orchestrates).
- **Auth Service** (revokes tokens, synchronous).
- **Billing Service** (cancels, refunds, queued).
- **Integration Manager** (webhook queue + retry).
- **Audit Log** (immutable).
- User-facing status page (read-only progress tracker).

---

## END_TS
1781056713
