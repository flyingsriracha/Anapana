## REFLEX
Without this process, my answer would be: list the obvious steps — confirm dialog, soft-delete with grace period, cascade billing cancellation, GDPR compliance, and return data export.

## TIER
STANDARD — T1 (cross-system: auth, billing, integrations, compliance all touched) + T2 (framing suppressor: "greenfield, no spec" feels like freedom but obscures that B2B team-account deletion is fundamentally different from B2C). T3 exempted: pure advisory task, reversibility sits with the human.

## ANSWER

**The hinge the obvious answer misses: "delete my account" means different things depending on who is asking.**

In a B2B SaaS with team accounts, there are at least three distinct actors who might trigger a deletion flow, and each has a different blast radius:

1. **Individual seat holder** — wants to leave a team. Data they created may belong to the org. They can't unilaterally delete org data.
2. **Team/org admin** — wants to delete the workspace. This affects every member, all integrations, and the billing contract.
3. **Billing owner** — may or may not be the same as the admin. Canceling billing ≠ deleting data.

Conflating these is the most common B2B account-deletion design mistake. The UI says "delete my account"; the implementation has to know which of those three flows it's executing.

---

### Considerations, in order of how often they're underweighted

**1. Ownership transfer as a pre-condition, not an afterthought**

If the person requesting deletion is the org owner or the only admin, the deletion flow must force ownership transfer or an explicit "dissolve organization" choice before proceeding. Deleting the owner account without this orphans the team — remaining users can't manage billing, can't invite people, can't export their own data. This is the silent failure mode that generates support tickets and chargebacks.

Questions to answer before building:
- Can an org have multiple owners? If not, who can be promoted?
- What happens to a team of one (solo workspace)?

**2. Data taxonomy: what actually gets deleted**

Three categories, each needs a policy decision:

- **Personal data** (email, name, preferences, auth credentials) — must be deletable on request under GDPR/CCPA. Clear deadline: 30 days is the norm.
- **Org-owned content** (documents, projects, shared assets) — belongs to the organization, not the user. Deleting a seat holder should not delete this. Deleting the org should prompt "export first" with a hard deadline.
- **Audit logs** — often legally mandated to retain for 3–7 years even after an account closes. Deletion of personal identifiers from logs (pseudonymization) is not the same as deleting logs.

**3. Billing and contractual obligations**

A deletion request does not terminate a paid contract. You need to handle:
- Proration and refund policy (or not — this is a business decision, not a technical one, but the system has to enforce it)
- Seats that are on annual contracts — what happens mid-cycle?
- Notification to the billing contact before deletion takes effect (required for most payment processors' chargeback protection)
- Whether "delete" and "cancel subscription" are one flow or two

**4. Third-party integrations**

This is the one most product specs forget entirely. The account likely has:
- OAuth tokens granted to third-party apps (Slack, Salesforce, GitHub, Zapier, etc.)
- Webhooks sending data to external endpoints
- API keys issued to integrations

On deletion, you must revoke all active OAuth grants and API keys, and ideally fire a webhook event to integrations so they can clean up on their end. If you don't, third parties may continue attempting to call your API with dead credentials — that's a data-hygiene and security issue, not just a UX one.

**5. Grace period design**

Soft-delete with a hold period (7–30 days is standard) is the right default, but the design choices matter:
- During the grace period, can the user log back in and cancel? (Almost always yes — this is the undo window.)
- Are integrations suspended immediately or at end of grace period? (Suspend immediately — otherwise a revoked user can continue operating via integrations.)
- Who gets notified at what points? (Day 0: confirmation email. Day N-3: final warning. Day N: deletion receipt.)

**6. Compliance and residual data**

Post-deletion, you will almost certainly still have:
- Backups containing the user's data (need a retention and overwrite policy)
- Analytics/telemetry with their user ID (pseudonymize, don't delete — you need the behavior data)
- Mentions of the user in other users' activity feeds ("Alice commented on...")

The law cares about identifiability, not presence. A pseudonymized record is usually compliant. Document your interpretation and have counsel sign off.

---

### Questions I'd ask before building a single line of code

1. **Who can initiate each deletion type** (seat vs. org)? Is there a role model already, or does this define it?
2. **What's the contractual relationship with the org vs. the individual?** (Your ToS likely has an answer — read it first.)
3. **Do you have a legal hold requirement?** Some enterprise customers will require you to freeze deletion during litigation. Does your tier model include this?
4. **Which jurisdictions are you operating in?** GDPR (EU), CCPA (California), LGPD (Brazil), PIPL (China) all have different timelines and scope. Are you global?
5. **What do third-party integration partners expect?** Check the partner agreements — some require notification of account closure within a specific window.
6. **Is there a self-serve path, or is this ops-assisted?** Enterprise accounts deleting often go through account management, not a button. Which segment is this feature for?
7. **What's the export story?** You can't delete responsibly without a working data export. Does one exist?

---

### Tensions worth naming explicitly

- **User privacy vs. team continuity.** A user's right to deletion can conflict with their teammates' right to a functioning workspace. There's no clean technical resolution — only a policy decision about which wins, and under what conditions.
- **Simplicity vs. compliance.** A single "delete account" button is clean UX. GDPR, audit retention, and billing proration make the actual behavior anything but simple. The interface hides complexity; it doesn't eliminate it.
- **Immediate effect vs. grace period.** Users want deletion to feel instant (privacy assurance). Operations wants a hold window (chargeback, mistake recovery). The right answer is: immediate *revocation of access*, delayed *destruction of data*.

---

### Suggested approach order

1. Lock the data taxonomy first — what's personal, what's org-owned, what's legally retained.
2. Define the actor model — which roles can trigger which deletion type.
3. Design the ownership-transfer blocker — this is the gate before any deletion proceeds.
4. Build the integration revocation path — revoke tokens and keys on day 0, not day N.
5. Implement the grace-period state machine — suspended, not deleted, with clear reactivation path.
6. Wire up the compliance trail — deletion request logged, steps logged, completion logged.
7. Then build the UI — it's the last thing, not the first.

## END_TS
1781056702
