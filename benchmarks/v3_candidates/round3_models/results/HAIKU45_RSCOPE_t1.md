## REFLEX
Without this process, I'd give a quick list of technical steps (soft delete, data retention, billing sync) and miss the actual governance tensions.

## TIER
STANDARD (frame + trace; multi-system, high rollback cost, policy-driven)

## ANSWER

A B2B SaaS account deletion feature must balance three irreducible tensions: **Compliance** (legal must keep tax/invoice records) vs. **User control** (customer wants to be forgotten); **Reversibility** (recover from mistakes) vs. **Finality** (deletion is real); **Team data preservation** (members don't lose work) vs. **Completeness** (no traces remain). No single design resolves all three—your design is a policy choice among them.

**Recommended starting point (if unconstrained):** Export-first design with state machine (`active` → `deletion_requested` [7-day grace] → `soft_deleted` [anonymized, 30 days] → `hard_deleted` [purged]). Hold mechanism blocks deletion at `soft_deleted` if invoices/disputes/compliance holds exist. Deletion cascades only to user's profile and keys; team-owned resources stay with team. Full audit trail (who, when, why, approval).

**Critical questions to lock down before building:**
1. Regulatory baseline: GDPR? CCPA? HIPAA? SOX? Other jurisdictions?
2. Billing holds: Can we refuse deletion if invoices are open? What about mid-contract?
3. Team ownership: What's *personal* data vs. *team* data? Who owns projects/docs/API keys?
4. Support escalation: Do high-value accounts get human review before deletion?

Once those 4 answers are fixed, the feature design becomes mostly mechanical. The real work is surfacing the policy trade-offs and getting stakeholder alignment—not the code.

## END_TS
1718130000
