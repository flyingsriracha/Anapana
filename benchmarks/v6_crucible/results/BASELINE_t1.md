RED-TEAM REVIEW — Self-serve password reset design
SEVERITY LEGEND: CRITICAL / HIGH / MEDIUM / LOW / NITPICK

## CRITICAL: Broken token scheme
1. **MD5 is not a token generator.** `md5(email + date.today())` is predictable; an attacker who knows/enumerates the email computes the valid token offline in ms. Any party who knows the victim's email can reset without receiving the email.
2. **No secret component.** A reset token needs server-only entropy (`secrets.token_urlsafe(32)` stored, or HMAC keyed on a server secret). This has neither; "deterministic without storage" removes the property that makes tokens secure.
3. **Valid for the entire calendar day, every timezone.** Up to ~24h window; an attacker who obtains the token has hours to use it; midnight/timezone edges.
4. **MD5 collision risk.** MD5 is broken; indefensible in any security-critical path; fails audit.

## CRITICAL: Reset URL logged in plaintext
`log.info(f"sending reset url: {url}")` writes the full URL incl. token to logs (centralized, retained, exported). Anyone with log access can reset any user → full account-takeover primitive in logs. Remove entirely; at most log a hashed/truncated address.

## HIGH: Email address in the query string
`/reset?token=<token>&email=<e>` → browser history, Referer to third-party scripts, CDN/LB/proxy logs, extensions. Email not needed if token is stored server-side; if stateless retained (shouldn't be), put email in POST body.

## HIGH: Rate limiting is wrong in multiple ways
a. Counter never resets → user who forgets 6× over a lifetime is permanently locked out. b. Wrong axis — per-user cap doesn't stop an attacker rotating across victims, or one who computed the token offline, or enumeration. c. Lockout response differs from non-existent-account response → leaks email existence. d. No IP-level/global rate limit/CAPTCHA described.

## HIGH: No token expiry beyond "end of calendar day"
Should expire in 15–60 min and be single-use. Here: calendar-day scope (~24h), no use-invalidation, no invalidation of old tokens on new request (moot since MD5 is identical, but shows no lifecycle thinking).

## HIGH: No CSRF protection described
/forgot-password and /reset need CSRF defense. An attacker page can POST to /forgot-password from a third-party origin → resets/spam/disruption.

## HIGH: `notifications` queue shares infra with product emails
One notification per session into the same queue as product emails/push/digests → a user with many sessions (or an attacker looping before the limit) floods the queue; security-critical "password changed" shares fate with marketing digests; no priority/isolation.

## MEDIUM: No email verification on signup implied
If emails aren't verified at signup, /forgot-password becomes an arbitrary-email spam vector.

## MEDIUM: Migration unsafe for large tables
`ALTER TABLE ... ADD COLUMN NOT NULL DEFAULT` rewrites/locks on older Postgres/large tables; no zero-downtime strategy (nullable + batch backfill + constraint).

## MEDIUM: Sign-out-everywhere race condition
Loop revokes then enqueues with no transaction; crash mid-loop → partial revocation; a concurrent request between read and revoke may succeed. Use atomic op / session-generation counter.

## MEDIUM: Sign-out-everywhere UX undiscussed
Disruptive for a user logged in on 10 devices; mobile re-auth may look broken; current session handling unspecified.

## MEDIUM: No HTTPS enforcement / interception
References https but doesn't assert/enforce; email link-preview bots may consume the token.

## LOW: POST endpoint takes email as query param `e`
POST should take email in body, not URL (logs/history/referrer). `e` single-letter name in a security handler hurts audit.

## LOW: `{"ok": True}` may not be valid JSON
Python bool vs JSON `true` depending on framework — check serialization.

## LOW: Open OAuth/Auth0 question unresolved before merge
Process failure in a "final rubber-stamp" doc; if "yes" the design is obsolete; if "no" record why.

## LOW: Account enumeration beyond happy path
Email-delivery timing oracle; rate-limit enumeration channel; malformed-email response codes unspecified.

## NITPICK: "Reviewed and approved" framing creates false confidence
Discourages reviewers; a doc with a Critical auth vuln was "approved by two seniors." Remove such framing — it substitutes social pressure for rigor.

## SUMMARY TABLE
CRITICAL: token=MD5(email+date) predictable; reset URL logged. HIGH: email in URL; rate-limit (never resets/wrong axis/enumeration); token ~24h no single-use; no CSRF; security notifications share queue w/ marketing. MEDIUM: email maybe unverified; migration lock; session loop race; sign-out UX; HTTPS not asserted. LOW: POST email in URL; `{"ok":True}` JSON; OAuth question unresolved; timing oracle. NITPICK: approved framing.

Bottom line: two Criticals (computable token; logged token) = full account-takeover primitive. Must not merge. Redesign the token from scratch (cryptographically random, stored, short TTL, single-use). Address all other findings in the same pass.
