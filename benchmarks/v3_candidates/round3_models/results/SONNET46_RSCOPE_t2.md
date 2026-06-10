## REFLEX
Without this process, my answer would be a comprehensive list of considerations (legal/compliance, data dependencies, soft deletes, billing edge cases, downstream integrations) organized into sections — probably 8-10 bullet clusters with no prioritization of tensions or clarifying questions that gate the design.

## TIER
STANDARD

## ANSWER

**First: "account" is ambiguous in B2B SaaS — this is the gate question before design begins.**

In a team-account model there are at least two distinct features that get called "delete my account":

1. **Member deletion** — an individual leaves or is removed from a team. Billing continues. Data ownership transfers or is deleted. Permissions revoked. This is relatively contained.
2. **Organization/team account deletion** — the billing entity closes. All members lose access, all data is scheduled for removal, the billing relationship ends, integrations are severed. This is high-blast-radius and largely irreversible.

These require different flows, different authorization models, and different support burden. Conflating them is the most common early-stage mistake. Clarify which (or both) before writing a line of spec.

---

**Assuming both are in scope, here is the design terrain:**

### Who can do it, and under what authorization?

For member deletion: the member themselves, and admins with appropriate role. For org deletion: typically only the account owner (billing contact), not just any admin. This distinction matters — a disgruntled admin should not be able to delete the organization. Require re-authentication (password or MFA prompt) immediately before the destructive action, not just session auth.

### What does "deleted" actually mean, and when?

Soft delete with a grace period is almost always correct. Hard immediate deletion is a support disaster — the first ticket you get is "I deleted by accident, can you restore it?" A 30-day grace period with clear UI state ("Your account is scheduled for deletion on [date] — cancel anytime") covers the vast majority of cases. During grace: login should still work (so they can cancel), but new data creation should be gated or blocked. Define this explicitly.

### Billing: when does it stop?

This is the sharpest tension in the design. Options:
- Stop billing immediately on deletion initiation (user-friendly, creates refund/proration complexity)
- Bill through the current period, then stop (cleaner financially, feels punitive if the user pays monthly and deletes on day 2)
- Stop billing at grace period end

The choice should be a business decision, not a technical default. Make it explicit in the spec. Whichever you pick, the confirmation flow must state it clearly: "Your billing will end on [date]. You will not be charged after that."

### Data: what happens to it, and what must the user receive first?

Before deletion, users should be able to export their data — not as a nice-to-have but as a legal requirement in GDPR jurisdictions and a trust requirement everywhere else. The export should be available during the grace period. After hard deletion, what's actually deleted vs. retained? Audit logs often must be retained for regulatory or contractual reasons even after account deletion. Payment records must be retained for tax purposes (typically 7 years in the US). Third-party integration data (data you pushed to or pulled from external services) is not yours to delete — be clear about what the deletion covers.

### Third-party integrations: what breaks, and does anyone know?

When a team account is deleted, every active integration — webhooks, OAuth tokens, API keys, connected apps — is severed. If you have integrations (Slack, Salesforce, custom webhooks), those integrations may have active workflows that break silently on the other end. The design should: (a) list all active integrations clearly in the deletion confirmation flow, (b) require explicit acknowledgment ("I understand my Slack integration will stop working"), and (c) consider sending a notification to the connected service if their API supports it.

### Cascading team membership: what happens to other members?

When an org account is deleted, every member of that team loses access. Do they know? They should receive notification before the account is deleted (not just the owner), with enough time to export their own work. The confirmation flow for the owner should state how many members will be affected and that they will be notified.

### The confirmation flow itself

The highest-risk moment is when a user is in the confirmation screen. Anti-patterns to avoid:
- "Are you sure?" with two identical-looking buttons — dark pattern and support liability
- Asking them to type "DELETE" with no explanation of consequences
- Burying the consequences in fine print

What works: a summary screen that lists the specific consequences (X members will lose access, Y integrations will be severed, your data will be deleted on [date], billing will end on [date]), a required acknowledgment checkbox per major consequence, and a 24-48 hour email confirmation link before anything is actually scheduled. This is not bureaucratic friction — it is a support cost reducer.

### Deletion state machine

Sketch the states explicitly before implementation:
`active → deletion_requested → grace_period → deleting → deleted`

Each state needs defined behavior: what can the user do, what can admins do, what does the product show, what do integrations see, what does the API return for requests from deleted-account tokens?

---

**Questions I'd ask before building:**

1. Are we designing member deletion, org deletion, or both? Which is P0?
2. What is the grace period length? Is it configurable per plan (enterprise gets 90 days, free tier gets 7)?
3. What is the billing cutoff policy — initiation, end of period, or end of grace?
4. Which data must be retained post-deletion for legal/compliance reasons, and who owns that spec (legal, not engineering)?
5. Do we have a data export feature today? If not, does deletion block on it being built?
6. Which integrations are in scope for the first release? Are there integration owners on the other side who need notification?
7. Who holds the "owner" role on a team account, and what happens if they're the only member when they request deletion — is that a special case?
8. What's our support load target? (Grace period length, notification coverage, and confirmation flow complexity are all knobs that trade user-friction for support tickets.)

## END_TS
1781056702
