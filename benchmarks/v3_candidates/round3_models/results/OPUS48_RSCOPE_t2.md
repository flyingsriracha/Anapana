## REFLEX
A feature checklist treating "delete account" as one well-defined action: confirm modal, soft-delete + grace period, cascade-delete the data, cancel billing, revoke integration tokens, send a confirmation email, satisfy GDPR.

## TIER
FULL — Cross-system by nature (identity, billing, integrations, team data). The advisory output is reversible, but the operation being designed is the most irreversible in the product, and "delete *my* account" in a multi-tenant B2B context is a textbook under-specified frame. Borderline STANDARD→FULL, rounded up because the framing fork is the heart of the question.

## ANSWER

Before any of the mechanics, there's a fork in the requirement that determines almost everything downstream: **"delete my account" is not one feature in a B2B product — it's at least three.** The phrasing borrows from consumer apps where account = user = data owner. In your world (team accounts, billing, integrations) those three come apart, and which one you mean changes the data model, the legal posture, and the UX:

1. **A member leaves an org.** Someone on a team removes themselves (or is removed). Their *login* may survive — they could belong to other workspaces. Their *authored content* (tickets, comments, files) usually must NOT be deleted, because it belongs to the org, not to them. This is really "remove membership + reassign/anonymize authorship," not deletion at all.

2. **An org/workspace is deleted.** The owner shuts down the whole tenant. This is the big, dangerous one: it cascades across every member, all shared data, the subscription, and every integration. This is the operation people actually fear.

3. **An identity is closed.** A person wants their *personal login and PII* gone everywhere. If your auth is shared across orgs, this is a cross-tenant operation and collides hardest with data you're legally required to keep.

If I built a single "Delete my account" button without resolving this, I'd ship the wrong thing — most likely conflating (1) and (2), so a member "deleting their account" either orphans org data or, worse, can nuke a workspace others depend on. **So the first deliverable isn't code; it's deciding which of these you're funding, and naming the other two explicitly so they're not accidentally bundled.**

Here's how I'd approach it once that's settled.

### Model deletion as a state machine, not an endpoint
The instinct is a synchronous "DELETE → rows gone." For anything destructive at this blast radius, model it as a lifecycle: **`active → scheduled_for_deletion (soft-delete, grace window) → purging → purged`**, driven by a durable background job, not the request that the user clicked. Reasons:

- **Reversibility where it's cheap.** A grace window (commonly 14–30 days for orgs) turns "I rage-quit / got phished / fat-fingered it" into a recoverable event. During the window the account is invisible and inert but restorable.
- **The actual purge is hard and slow.** It touches many stores (primary DB, search index, blob storage, caches, analytics warehouse, backups, logs, downstream integrations). A button can't do that atomically; a tracked job with retries and a completion record can.
- **You can prove it finished.** Emit an audit/erasure record when `purged` is reached. You will eventually need to answer "did we actually delete X, and when?" — for a regulator, an enterprise customer's security review, or a dispute.

### The sole-owner trap (the one most teams miss)
The single highest-value guardrail: **what happens when the person deleting is the only owner/admin/billing contact of an org?** You cannot let them orphan a workspace that other paying members still use. So self-deletion for an org owner must be *gated*: force ownership transfer first, or require explicitly choosing "delete the entire workspace and everyone in it" as a separate, heavier confirmation. Conflating "I'm leaving" with "destroy the org" is how you get catastrophic, unrecoverable support tickets.

### Billing has to settle, not just stop
"Cancel the subscription" is the easy half. The questions that actually bite:
- Is there an **in-flight balance** — metered usage this period, an unpaid invoice, a disputed charge? Deletion shouldn't be an exit hatch from owed money, and you can't delete the records you'd need to collect or reconcile.
- **Refund/proration policy** on mid-cycle deletion — decide it before building, because it changes what you must retain.
- **Financial records are a retention obligation,** not user data you're free to erase. Invoices and tax records typically must survive account deletion for years. This is the first place "delete everything" and "the law says keep it" collide.

### Third-party integrations: revoke *and* reckon with data already gone
Two distinct problems:
- **Revoke outbound:** kill OAuth tokens / API keys you hold, deregister webhooks (so you stop firing events into a void and stop ingesting), and on a clean teardown, best-effort de-register the connection on their side. A token you forget to revoke is a live credential after the account is "gone."
- **Data that already left your perimeter:** if you've synced their data into Salesforce/Slack/an analytics tool/a customer's warehouse, *you cannot delete that by deleting your account.* You can only stop sending and, where you control it, recall it. This has to be stated honestly to the user and is a real limit on any "we deleted everything" promise.

### GDPR/CCPA: "close my account" ≠ "erase my data," and they can conflict
Treat these as related but distinct:
- **Erasure (right to be forgotten)** has a clock ("without undue delay") and demands PII actually disappear — including from backups and logs, eventually.
- **Retention obligations** (financial, tax, fraud/abuse evidence, legal hold) require you to *keep* specific data.
The resolution is almost always: hard-delete/anonymize PII, **retain a minimal, lawful, often pseudonymized record** for the things you're required or permitted to keep (invoices, abuse history, audit trail of the deletion itself). Backups are the gnarly bit — you rarely surgically edit backups, so the standard answer is documented backup rotation (the data ages out within N days) plus a suppression list so a restore can't silently resurrect a deleted person. Decide and write down which data is erased, which is retained, on what legal basis, and for how long.

### Make the destructive act deliberate and authenticated
Friction here is a feature: re-authenticate (or step-up) before a destructive delete, type-to-confirm the org name for tenant deletion, and require it be the right *role* (owner, not any member). Send a confirmation email **with the grace window and a one-click "cancel deletion" / restore link** — that email is your safety net against both mistakes and account takeover.

### Tensions worth stating out loud
- **Reversible vs. truly gone.** A grace window is good UX and safety, but a user demanding GDPR erasure wants the clock to *start*, not a 30-day limbo. You likely need two paths: soft "close my account" (reversible, grace) and explicit "erase my data" (honors the legal timeline). Don't force one to be the other.
- **Clean cascade vs. preserving org/financial truth.** The more thoroughly you delete a member, the more you risk corrupting org data and breaking retention. Anonymize-and-retain usually beats hard-delete for *authored* content.
- **Self-serve vs. safety.** Fully self-serve org deletion is great until someone deletes a workspace 40 colleagues rely on. Gating + transfer + grace is the compromise.
- **"We deleted everything" vs. reality.** Backups, legal holds, and data already pushed to third parties mean you almost never literally delete everything immediately. Your copy and your DPA should promise what's actually true.

### Questions I'd want answered before writing code
1. **Which of the three** are we building first — member-leave, workspace/tenant delete, or identity/PII erasure? Are the other two explicitly out of scope or just unmentioned?
2. **Auth topology:** can one login belong to multiple orgs? (Decides whether identity deletion is single- or cross-tenant.)
3. **Who's allowed** to trigger each, and what's the sole-owner rule — block, force transfer, or escalate to "delete the org"?
4. **Grace window:** are we offering one, and how long? Different for members vs. orgs?
5. **Billing policy** on mid-cycle deletion: settle outstanding balance first? proration/refunds? which financial records must we retain and for how long?
6. **Regulatory scope:** which regimes are in play (GDPR/CCPA/sector-specific), and do we need a *separate* legally-clocked erasure path distinct from account-close?
7. **Retention/backup reality:** what's our backup rotation, and do we have (or need) a suppression list so restores don't resurrect deleted data?
8. **Integration inventory:** which third parties hold synced data, and what does "we stopped sending" honestly mean for data already there?
9. **Enterprise contracts:** do any customer DPAs/MSAs specify deletion SLAs or retention terms that override the default?
10. **Audit:** what deletion evidence must we keep, and who needs to query it (support, security review, regulator)?

My honest recommendation: **scope it to one operation first** (most often "delete a workspace," since that's the scary, high-demand one), build it as a soft-delete → grace → purge state machine with the sole-owner gate, a settled-billing precondition, token/webhook revocation, and a documented erase-vs-retain data map — and treat member-leave and full PII-erasure as their own designs rather than letting them ride on the same button.

(One caveat on grounding: there's no codebase here to inspect, so the above is reasoned from common B2B SaaS patterns rather than verified against your actual data model, auth setup, or contracts — several of the questions above exist precisely to replace my assumptions with your facts.)

## END_TS
1781056713
