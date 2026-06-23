# Account Deletion Feature — Design Analysis

## Step 1: Reflex First
Without this process, my answer would be: *"Build a confirmation dialog that soft-deletes the user, with a 30-day grace period for recovery, then hard-delete via cron job."*

This is the standard pattern I'd reach for — it's what most SaaS platforms do. But I need to check whether that default actually fits a B2B team-account context.

---

## Step 2: Triage

- **T1 multi-file/cross-system?** Yes — touches auth, billing (Stripe/etc.), integrations (APIs, webhooks), team management, data pipeline, GDPR compliance. System-level concern.
- **T2 framing pressure?** "Greenfield, no existing spec" — zero constraints is a pressure itself (over-build risk). B2B team accounts — could push me toward enterprise-grade when simpler might work.
- **T3 expensive to roll back?** Yes — actual data deletion is irreversible; billing changes can cause cascading failures.

**Tier → FULL.** (Borderline STANDARD, but cross-system + irreversible data loss + billing = round up.)

---

## Step 3: Frame Check

**A. What is the prompt asking me NOT to consider?**
- The prompt starts from "we need to build this" — it never asks *whether* we should, or what problem it solves. It frames deletion as inherently good.
- It doesn't ask about *account vs. user* in a team context — this is the critical ambiguity. "Delete my account" means different things for an admin vs. a regular team member.
- It doesn't ask about *why* they're leaving — which could be product feedback we're foregoing.

**B. Actual problem or symptom?**
The actual problem: users want to leave. But *why* is the interesting question. Building deletion means accepting churn. A full design should surface whether there's an off-ramp to understand churn *before* data destruction.

**C. What pressure is on me?**
Pressure to produce a comprehensive design for a "simple" feature that's actually quite complex. Pressure to show I understand B2B SaaS nuances. No named deadline but "greenfield" invites over-engineering.

**Reframe check:** The stated task (design account deletion) is the right task — but I must *explicitly* handle the team-account vs. individual-account distinction, which the prompt didn't call out. That's the hidden fork.

---

## Step 4: Trace (Zoom Discipline)

**System level:** B2B SaaS with team accounts, billing, third-party integrations
- **Failures if wrong:** Cancelling billing when only one user leaves → company loses access they paid for. Deleting integrations → other team members lose workflows. GDPR/CCPA violation if data isn't actually removed.

**Module level:** Auth system, billing system, integration layer, user data store
- **Failure if wrong:** Team admin deletes account → wipes all users' data without consent. Individual user deletes → leaves dangling records, breaks team billing seat count.

**Behavior level:** What does "delete my account" mean semantically?
- For a team member (not owner): leave the team, remove personal data, no billing impact
- For the last/sole admin: this IS company deletion
- For a team owner with other admins: transfer ownership OR confirm company deletion

**Fix altitude:** The core design decision is the *deletion type branching* — what entity is being deleted and who has authority. Build a decision tree at the system level before writing any code. The module-level implementations (billing, data purge, integrations) are downstream of that tree.

---

## Step 5: Reproduce-Gate

**Predict the failure (open-form):**
*If we implement a single "delete account" button that asks for confirmation and then deletes, in a B2B team context we will:*
1. Allow individual team members to disrupt company billing by deleting their seat (leaving the company paying for ghost seats or triggering incorrect proration)
2. Allow a junior admin to destroy the whole company's data without oversight
3. Drop third-party integrations that other team members depend on
4. Lose the ability to understand churn because we destroyed the data before asking why

**Non-code grounding:** I can't run code for a greenfield design. The predicted failure mode is logical — it follows from the fundamental ambiguity of "account" in a multi-tenant system. This is a design hypothesis, not a finding. Proceeding with the design on the assumption this failure is real.

---

## Step 6: FULL Tier — Inversion & Alternatives

### How would I make this worse?
1. **Make it instantaneous with no recovery** — "You asked to delete, it's gone." Maximum data loss on mistakes.
2. **No team role check** — Anyone with an account can delete the team. Maximum chaos.
3. **Delete without billing reconciliation** — Customer gets charged after data is gone, or refunds happen without data removal (double liability).
4. **Skip the churn survey** — Destroy all evidence of *why* they left, blinding product to churn patterns.

### Alternatives (including "fix elsewhere" / "do nothing")

**Alternative A: Deactivate-only (no hard delete)**
- Approach: Set a flag, revoke access, keep data indefinitely. Respond to GDPR deletion requests ad-hoc.
- Downside: Data liability grows forever; not compliant with "right to deletion" timelines without manual process.
- Silent failure: Team thinks data is gone but it's accumulating, and a breach exposes "deleted" user records.

**Alternative B: User-level delete only; team-level disable-only**
- Approach: Users can delete themselves (leave team, remove personal data). Team can only be disabled, not deleted; must contact support for hard team deletion.
- Downside: Admin frustration at not having a self-serve off-ramp; support load increases.
- Silent failure: Accumulation of disabled-but-not-deleted teams creates support debt and data liability.

**Alternative C: Fix elsewhere — improve team management (roles, transfer ownership) first**
- Approach: Before building deletion, ensure teams can manage admins and transfer ownership. Then deletion is just the final step in a mature lifecycle.
- Downside: Delays the deletion feature; teams may churn waiting for it.
- Silent failure: Never builds deletion because team management is never "done" — feature stalemate.

**Alternative D: Do nothing — require support ticket for all deletions**
- Approach: No self-serve deletion. User emails support, team verifies, engineer deletes manually.
- Downside: Terrible UX, high operational cost, violates user control expectations, GDPR issues with response times.
- Silent failure: Support team develops informal "delete" processes that bypass compliance; no audit trail.

---

## Step 7: Identity (Reflex vs. Proposal)

**Reflex (what I would have said without discipline):**
> *"Build a confirmation dialog that soft-deletes the user, with a 30-day grace period for recovery, then hard-delete via cron job."*

**Proposal (what the discipline produced):**

The design is *not* a single feature — it's a **decision tree** rooted in who the user is and what entity they're acting on:

**Decision flow for "Delete my account":**
1. **Who is the user?** → Check if they're a team owner, admin, or regular member
2. **Is there a team?** → If yes, is this the last admin? Are there other members?
3. **What billing impact?** → Prorate seat? Cancel plan? Notify billing system?
4. **What integration impact?** → If team delete, revoke all OAuth tokens? If user delete, which integrations are personal vs. team?

**Minimum viable design:**
- **Regular member:** Delete themselves from team (remove personal data, free seat, revoke personal API keys). No billing change. Team continues.
- **Team owner only:** Full account deletion (cancel billing immediately with prorated refund, purge all team data, revoke all integrations, 30-day grace where billing is paused but data is restorable by contacting support, then hard delete).
- **Admin (not owner):** Must transfer ownership first or contact support. Cannot unilaterally delete the team.

**Key non-obvious considerations the reflex missed:**
- Integration revocation cascades (revoking a Slack app might disrupt the whole company's workflow)
- Billing reconciliation timing (don't issue a refund if payment is still processing)
- Audit trail (who initiated deletion, when, what was the reason)
- GDPR/CCPA "right to deletion" vs. the grace period (30-day restore window needs legal review)
- Grace period UX (communicate clearly that data will be destroyed, don't mislead that "it's fine, we kept it")
- Team member notification (when someone deletes themselves, should the team admin know?)
- Data portability offering (offer export *before* deletion — reduces support tickets from users who just wanted their data)

**The delta is visible:** The discipline pushed me from "standard soft-delete pattern" to a context-aware, role-based branching design. The single biggest change is recognizing that "account" is ambiguous in a team context, and the default pattern would have been dangerously wrong for the B2B use case.