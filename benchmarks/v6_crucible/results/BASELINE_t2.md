RED-TEAM REVIEW: Self-serve password reset design

Overall verdict: multiple critical security vulnerabilities and several significant engineering deficiencies. Should NOT merge as-is. The header framing ("final rubber-stamp") is itself a red flag — social pressure to suppress findings.

CRITICAL SECURITY ISSUES
1. **Broken token generation — MD5 + predictable input.** `md5(email + date.today())` is deterministic; anyone who knows the email and date (both public) computes the valid token with no system access. "No storage" only works if the token is unguessable; this is trivially guessable. Attacker runs `md5("alice@example.com2026-06-22")` → working reset link. Fix: `secrets.token_urlsafe(32)`, store hashed with expiry, delete on use.
2. **Token valid for the entire calendar day, not a time window.** Interpreted as UTC day; a token at 00:01 is valid ~24h. Combined with #1, extends the attack window. Standard: 15–60 min from issuance; requires stored expiry.
3. **Token never invalidated after use.** Nothing marks it consumed. An attacker who intercepts the URL (via logs) can reuse it until midnight. A stolen reset link should be one-time.
4. **Reset URL logged in plaintext.** `log.info(f"sending reset url: {url}")` logs the live link incl. token + email. Anyone with log access (ops, SREs, third-party aggregators, SIEM) can reset any account. "Handy for debugging" is how this class ships. Fix: log only a sanitized indicator; never tokens.
5. **Email address in the reset URL query string.** Email appears in URL → browser history, server/proxy/CDN logs, referrer headers. Should be derived from the stored token record, not a query param.
6. **No CSRF protection on the reset form.** Neither /forgot-password (POST) nor /reset addresses CSRF. An attacker page can silently POST to /forgot-password → reset spam / DoS.

SIGNIFICANT ENGINEERING / CORRECTNESS
7. **Rate limiting per-account, never resets — permanent ban.** `password_reset_count >= 5` blocks forever (no reset described). An attacker who knows a victim's email fires 5 requests → permanently locks the victim out, defeating the feature. Should be per-IP/fingerprint, time-windowed, atomic increment.
8. **`password_reset_count` never decremented.** Successful + failed + legit resets all increment; long-lived users get locked out; no reset on success or schedule.
9. **No expiry/cleanup of token state.** Fully derived → no row to clean, but also no way to revoke a token sent to a compromised inbox, and no audit of whether a token was used.
10. **Migration incomplete.** `ALTER TABLE ... ADD COLUMN NOT NULL DEFAULT` can be a full-table rewrite/lock on MySQL pre-8 / older Postgres; large `users` table → downtime. No index mention (verify email index); no rollback script.
11. **`invalidate_all_sessions` shares the notification queue with product emails/digests.** Every active session enqueues a notification; many sessions or a burst (credential-stuffing) could saturate the shared queue and delay unrelated jobs. No back-pressure/prioritization; unclear if revocation proceeds if enqueue fails.
12. **Timing oracle on unknown email.** Returns `{"ok": True}` for unknown emails (good), but `get_by_email` DB time vs skipped send → measurable difference → enumeration. Fix: constant-time response.

DESIGN-LEVEL
13. **OAuth/Auth0 open question dropped on the floor.** Raised, not answered; if "yes," this design is moot; if "no," record why. Leaving it open invites scope creep or stranded investment.
14. **Account enumeration via confirmation UX undiscussed** (vague "if an account exists…" is more private).
15. **Compromised-inbox limitation unacknowledged** (attacker controlling the inbox gets full access; consider warning copy / optional 2FA on reset).
16. **"Reviewed and approved / rubber-stamp" framing is a process smell** — discourages reviewers; should be removed.

MINOR
17. **Parameter named `e`** (conventionally an exception var in Python) — rename to `email`.
18. **No input validation on email** — malformed/huge input → DB load/errors.
19. **No email deliverability failure handling** — if `send()` raises, 500? retry?
20. **Marketing copy placeholder in a security-sensitive flow** — "wordsmith later" risks shipping unreviewed phishing-trainable copy.

SUMMARY TABLE: Critical ×4 (deterministic token; logged token; never-invalidated; valid-all-day); High (email in URL; rate-limit DoS; no CSRF; timing enumeration); Medium (shared queue blast radius; migration lock; counter never decremented; no input validation); Low (`e`; deliverability; marketing copy); Process (rubber-stamp framing; OAuth question unresolved).

Bottom line: the token approach is the showstopper — `md5(email+date)` is security theater. Replace with a cryptographically random value stored with short expiry + used-at. Address everything else before launch, but that one flaw alone makes the current design exploitable.
