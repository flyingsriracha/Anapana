## REFLEX  (one line — gut answer before applying the process)
Confirmation modal → soft-delete with a grace period → background purge job that cascades through the data stores.

## TIER
FULL — the topic is genuinely cross-system (identity, billing, integrations, legal) and the real-world feature is the one operation you can't undo, so it's worth the inversion + alternatives pass. (Blast radius of *this* answer is zero — it's advisory; the human builds. FULL here is about the thing being designed, not the act of designing it.)

## ANSWER  (natural expert reply; do NOT name the process/tiers)

Before designing anything, I'd push back on the brief — gently, because it hides the whole problem. "Delete my account" sounds like one feature: a button, a confirm, a row that goes away. In a B2B product with team accounts, billing, and third-party integrations, it isn't one feature. It's the *teardown half of your account lifecycle*, and almost every hard question lives in the gaps the phrase papers over. So the first thing I'd do is refuse to build a button and instead pin down four things: **who** is allowed to delete, **what** "delete" even means, **what has to survive** the deletion, and **what happens when a downstream step fails halfway through.** Get those wrong and you don't ship a feature, you ship an incident.

Let me walk the angles.

**1. The word "account" is doing too much work — separate the objects first.**
In a single-user consumer app, user = account. In your world there are at least three distinct things tangled together:
- **A user/identity** (a person, possibly a member of several orgs).
- **A membership** (that person's seat in one org).
- **The org/tenant itself** (the team account that owns the data, the subscription, the integrations).

"Delete my account" could mean *any* of these, and they're completely different operations. A member removing themselves from one team is routine and low-stakes. An owner deleting the *org* destroys data that belongs to everyone on the team and terminates a paid contract. If you build one flow that conflates them, you'll either let a junior teammate nuke the company workspace, or you'll make leaving a team as scary as bankruptcy. **Decision to force early: are we shipping "leave this team," "delete my user identity," and "close the org" as three flows, or one?** My default: three, with the org-closing one being by far the most guarded.

**2. Authorization — who can pull the trigger, and what about everyone else?**
This is the one people skip and regret. In a shared account:
- Org deletion should be restricted to **Owner/Billing-admin role**, and ideally require there be no ambiguity about who the owner is (sole owner, or explicit owner action). What happens if the only owner has left the company and nobody can delete? You need an answer (support-assisted path, or ownership transfer).
- What happens to the **other members'** data and access? They should arguably be *notified*, not just silently logged out one morning. There's a real product/ethics question: one admin's click can erase work for fifty colleagues. Consider a notice period, or at least a broadcast.
- **Re-authentication at the point of deletion** (password / SSO / step-up MFA), because this is exactly the action an attacker who's hijacked a session would love to perform — or to *prevent* you from undoing.

**3. "Delete" is at least three different promises — decide which you're making.**
- **Deactivate / suspend** — account closed, billing stopped, data retained, reversible.
- **Soft-delete** — marked deleted, hidden, recoverable for a grace window (e.g. 7–30 days), then purged.
- **Hard erasure** — the data is genuinely, irreversibly gone, including from backups and third parties (this is what GDPR/CCPA "right to erasure" actually demands).

These are not the same engineering problem, and you probably need **soft-delete with a grace period as the default UX**, plus a **true-erasure path** for legal requests. The grace period is doing real work: it's your insurance against rage-clicks, account takeover, and the "I didn't realize that would delete the whole team" support ticket. **Be explicit in the UI about which promise you're making** — "recoverable for 30 days" vs "permanently deleted" are very different commitments and users will hold you to the words.

**4. Billing has to settle, and it has its own retention rules.**
On delete you have to: cancel the subscription, decide on **proration/refund policy** (refund the unused period? forfeit? this is a business call, not an engineering one), settle any outstanding invoice or usage-based charges, and revoke API keys / tokens so usage actually stops. Crucially — **you cannot delete the financial records.** Invoices, tax records, and payment history are things you're legally required to *keep* (commonly 7 years), and your payment processor (Stripe et al.) keeps its own copy regardless. So "erase the customer" and "erase the billing history" are in direct conflict, and the resolution is: financial/transaction records are retained (often pseudonymized) even after the account is "deleted." Design for that from day one rather than discovering it during an audit.

**5. Third-party integrations are the part that fails silently.**
This is where a clean-looking delete leaves a long tail of garbage and security exposure:
- **Outbound:** revoke OAuth grants and API tokens you hold for *their* systems (Slack, Google, etc.), tear down webhooks, remove provisioned resources. If you don't, you keep access you no longer should have — a real security liability.
- **Inbound:** other systems may hold *your* tokens or call *your* webhooks. Those calls will start 404ing or, worse, hit a half-deleted account.
- **Data already shipped out:** if you've pushed their data into a warehouse, a CRM, an analytics tool, or a sub-processor, "delete" has to reach those too, or your erasure claim is false.
- These calls are **slow, rate-limited, and fail.** Which is the whole reason the next point matters.

**6. The mechanism: do it as an orchestrated, async, idempotent, resumable job — not a synchronous cascade.**
The instinct (my own first instinct) is "on click, cascade-delete everything." Don't do it synchronously. The right shape:
- Click flips state to **`pending_deletion`** immediately (access revoked, billing stopped, clearly reversible during the grace window).
- A **background workflow** then works through a checklist of steps — purge data store A, revoke integration B, settle billing C — where **each step is idempotent and individually retryable**, and the whole thing is **resumable** after a partial failure. Treat it like a saga, not a transaction. Half-deleted is the state you must design *for*, not against.
- **Log every step** (an audit trail of the deletion itself), because "we deleted everything we said we would" is a claim you'll need to prove — to the customer, to a regulator, to your own support team.
- **Verify and report**: when it's done, you should be able to say what was erased and confirm nothing dangling remains.

**7. What must NOT be deleted — the retention overrides.**
Counterintuitively, a big part of a delete feature is the list of things you *keep*: financial/tax records (above), data under legal hold or active litigation, fraud/abuse signals you need to block re-signup of a banned actor, security/audit logs, and anything a contractual or regulatory obligation forces you to retain. **User-requested erasure does not override a legal duty to retain** — and where they collide, retention usually wins, scoped and minimized. Your erasure should be "delete everything *except* the legally-required minimum, and document why each exception exists."

**8. Give them their data on the way out.**
Offer (or require) an **export before deletion** — it's good faith, it's often a legal right (data portability), and it dramatically cuts "wait, I didn't mean to lose that" tickets. Cheap to build relative to the goodwill and risk reduction it buys.

---

**The tensions worth naming explicitly (because they're where the real decisions are):**
- **Erasure vs. retention** — "delete all my data" collides head-on with "keep financial/legal records for 7 years." Both are obligations. You resolve it by scope, not by picking a side.
- **One member's action vs. the whole team's data** — in a shared account, one click can destroy others' work. Convenience for the admin vs. protection for everyone else.
- **Reversibility vs. genuine erasure** — a grace period (good for support and safety) is in direct tension with "permanently gone *now*" (what privacy law and security-conscious users want). You likely need both paths, clearly labeled.
- **Self-serve vs. assisted** — fully automated delete is a great experience and a great way to lose data irrecoverably to a hijacked session or a misunderstanding.

**And the honest alternative to building this at all (worth a serious look before you commit eng time):** for many early-stage B2B products, the right first move is *not* a fully automated self-serve org-delete. It's **self-serve deactivate + data export, with true erasure handled by a documented internal/CS process** triggered on request. You still meet your legal obligations, you avoid building the hardest, riskiest, most irreversible path before you have the volume to justify it, and you don't hand a session-hijacker a one-click company-deletion button. Build the full automated erasure pipeline when deletion *volume* — not deletion *existence* — demands it. The silent failure of going full-auto too early is that the rare catastrophic case (wrong person, wrong scope, no recovery) costs you more than all the support time you saved.

---

**Questions I'd want answered before writing a line of code:**
1. Which object are we deleting — a member leaving a team, a user identity, or the whole org? (I'd argue: three flows, not one.)
2. Who is authorized to delete the *org*, and what's the fallback when the only owner is gone?
3. Do we notify other members before their shared workspace disappears? Any notice period?
4. Soft-delete with a recovery window, true erasure, or both — and what's the window?
5. What's the refund/proration policy on mid-cycle cancellation? (Business decision.)
6. What are our actual retention obligations — tax, contractual, regulatory, legal hold — and which data do they cover?
7. Which third-party integrations hold our tokens or our customers' data, and what's the teardown order?
8. Do we offer/require a data export first?
9. Is this self-serve, or assisted-by-support for the first cut?
10. Which jurisdictions' privacy laws apply (GDPR/CCPA/etc.) — this sets the erasure SLA and the "what counts as deleted" bar?

Answer 1, 4, 6, and 9 first — they determine the shape of everything else.

## END_TS  (run: date +%s)
1781056682
