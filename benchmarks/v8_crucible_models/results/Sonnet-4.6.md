# Adversarial Review: Self-serve Password Reset

## 0. Triage
Trust-boundary auth flow: token generation, email delivery, session management, a shared queue, a DB migration. Hard to roll back once shipped. The "rubber-stamp" header is a suppression signal; ignoring it. Full pass.

## 1. Reflex + frame
Reflex (frozen): main risk is the token generation — cryptographically wrong, opens account takeover. Goals: self-serve reset; prevent unauthorized resets; prevent abuse (spam/enumeration/brute-force); minimize disruption on legit reset / kill sessions on compromise. Failure categories: correctness, security, data integrity (migration/race), performance/blast-radius (shared queue, live-table migration), failure/rollback, maintainability, user impact, adjacent systems. Out of scope: OAuth migration question, email provider internals, UI copy.

## 2. Steelman
Defensible simplicity: deterministic derive avoids a new table + cleanup job; "valid for the day" is shorter than many 72h links; session invalidation on reset is correct hygiene; rate-limit shows abuse awareness; `{"ok":True}` on unknown email prevents enumeration. A security-aware team making reasonable tradeoffs; many pieces are individually right.

## 3. Blind the framing
Ignoring "approved by two seniors / final rubber-stamp / no changes expected" — confidence signals, not correctness.

## 4. Premortem (5, across categories)
A. (security) Token guessable/forgeable — md5(email+date) deterministic, no server secret, tiny input space; attacker with the email computes valid tokens offline; account takeover. B. (security/data) Full reset URL incl. token + email logged at INFO → replicated to aggregators/third-party vendors → live tokens readable by many. C. (correctness/user) `password_reset_count` lifetime-cumulative, never reset → permanent lockout after 5 lifetime resets; if incremented per request, attacker locks a victim out with 5 requests (targeted DoS). D. (perf/adjacent) `invalidate_all_sessions` enqueues one notification/device onto the SHARED queue (product emails/push/digests); many devices or a bulk reset injects a burst degrading unrelated notifications; no isolation/backpressure — confirm at scale. E. (security/correctness) Token valid the whole calendar day; issued-at-11:59pm edge breaks at midnight; no revocation on use → same-day replay (reset at 10am, attacker reuses the token at 11am).

## 5. Turn the lens on myself
Over-weighted? Token weakness is genuine, appropriate. Under-weighted: migration lock risk (`ALTER TABLE ADD COLUMN NOT NULL DEFAULT` rewrites the table on MySQL pre-8 / Postgres pre-11 — engine unstated); rollback loses count data; email-in-URL is PII in web-server access logs + Referer headers (beyond finding B). Adding migration-lock + email-in-URL; keeping replay (part of E). Reflex was right but I didn't over-narrow (premortem spans ≥4 categories).

## 6. Findings — grounded, gated, ranked
**BLOCK F1 Keyless deterministic token → offline takeover.** Trigger: attacker runs md5(email+today) locally, calls /reset?token=..&email=target, sets password; no server interaction. Violated goal: prevent unauthorized resets. High×High (email is not secret — it's the login). Fix: random `secrets.token_urlsafe(32)`, server-side `password_reset_tokens` table (token_hash, created_at, used_at), short TTL (15–60m), one-time use. The table is the correct design.
**BLOCK F2 Full reset URL logged.** Trigger: `log.info("sending reset url: "+url)` every request → aggregator → any engineer/vendor extracts a live token → takeover before the user clicks (≤24h window). High×Medium (log access broader than account access). Fix: remove the URL; log only `user_id` + that an email was sent.
**BLOCK F3 No revocation on use → same-day replay.** Trigger: attacker observes the URL (forwarding rule, provider breach, F2 logs); user resets at 10am, attacker reuses the same token at 11am same day → resets again. Violated goal: tokens must be single-use. High×Medium. Fix: server-side token table with `used_at` (solves F1, F3, TTL together).
**THIS-SPRINT F4 Lifetime counter → targeted lockout.** Trigger: attacker submits 5 /forgot-password for a victim → victim permanently locked out of self-serve (back to support — the thing this feature removes); also legit users who reset 5× over years. High(lockout)×Medium. Fix: time-windowed limit (5/24h) + edge IP limit; drop the lifetime counter.
**THIS-SPRINT F5 Email in reset URL = PII in access logs / Referer.** Trigger: `/reset?token=..&email=..` → email in web-server access logs + Referer on navigation (broader distribution than app logs). Medium×High (every reset click). Fix: drop `email` from the URL; server resolves it from the token record.
**BACKLOG F6 Migration lock on large table.** Trigger: `ALTER TABLE users ADD COLUMN NOT NULL DEFAULT 0` rewrites/locks on MySQL pre-8 / Postgres pre-11 → login/registration degraded. Medium×Low-Med (engine unstated). Fix: confirm engine/version; online schema change (pt-osc/gh-ost) or add-nullable→backfill→constraint.
**THIS-SPRINT F7 Shared notifications queue (confirm at scale).** Trigger: forced bulk reset enqueues O(users×devices) into the shared product queue; low-priority reset notifications delay time-sensitive product ones. Medium×Low normal / Medium×Medium in breach response. Fix: separate queue or priority tier; batch with delay for bulk ops.
**HYPOTHESIS H1 Counter increment timing unshown** — before vs after email delivery? Before → a transient provider failure consumes a slot with nothing delivered. Investigate; decouple from delivery.

## 7. Reintegrate + verdict
Findings span auth/crypto (F1,F3), logging/trust boundary (F2), abuse/rate-limit (F4), PII (F5), deploy safety (F6), adjacent systems (F7). No step-1 category unrepresented. The three highest (F1,F2,F3) are all in the token design but are independent failure modes — not tunnel vision (F1 alone is enough to block). Reflex ("token generation is the main risk") confirmed, plus four secondary findings it alone would've missed.
**VERDICT: UNSOUND.** Three independent BLOCK issues each enabling takeover: keyless deterministic token (F1); logged reset URL (F2); no revocation/replay (F3). Root fix is the same: replace the stateless deterministic token with a cryptographically random token stored server-side (TTL + one-time use), and strip tokens from logs. Secondary (F4 counter, F5 email-in-URL, F6 migration) this sprint; F7/H1 investigate.
