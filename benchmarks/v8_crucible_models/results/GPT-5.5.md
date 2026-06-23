My gut says the main risk here is account takeover via reset-token design. I’ll audit that against the whole system rather than only the token code.

## Scope / system frame

This change creates a self-serve authentication recovery path. It touches a major trust boundary: an unauthenticated user can cause an authenticated credential change if they possess a valid reset link/token.

Primary goals/expectations:

- Correctness: legitimate users can reset passwords reliably.
- Security: attackers cannot reset another user’s password.
- Privacy: the flow must not leak account existence or reset credentials.
- Abuse resistance: attackers cannot spam users/support or lock users out.
- Data integrity/session safety: password changes invalidate old sessions reliably.
- Adjacent-system safety: email/notification queues and logs should not become credential sinks or abuse amplifiers.
- Operability/rollback: migration should be safe and rate limits should be observable/recoverable.

Out of scope: rewriting all auth to OAuth/Auth0 unless this design cannot be made safe incrementally. Email copy, handler variable naming, and docstrings are not material.

## Steelman

The design has the right high-level shape: email-based recovery, non-enumerating `/forgot-password` response, explicit session invalidation after reset, and an attempt to control abuse. Avoiding a new token table is operationally attractive, and “valid for the day” is a simple UX-friendly model. The team also recognized that password reset is part of the auth boundary and raised whether broader auth modernization is warranted.

## Premortem: how this could fail months after launch

1. Attackers compute reset tokens for known emails and take over accounts.
2. Reset links appear in application logs, log aggregators, support tooling, or incident dumps, giving staff or attackers password-reset capability.
3. Users or attackers exhaust `password_reset_count`, permanently blocking future resets or creating support burden.
4. A compromised/high-session account triggers many notifications and floods the shared notification queue, delaying unrelated product emails/push/digests.
5. The migration or counter semantics create rollout/rollback issues, especially if the users table is large or the count is never reset/incremented consistently.
6. Reset links leak via query strings in browser history, proxies, referrers, analytics, or email-security scanners.
7. The reset token can be reused all day, so a copied link remains dangerous even after a successful password reset.

Self-check: the token issue is indeed severe, but not the whole story. The broader risks are credential leakage through logs/URLs, abuse/lockout semantics, and shared-queue blast radius. I’m not going to spend time on naming/docstrings/email copy.

---

# Findings

## Block

### 1. Reset tokens are forgeable by anyone who knows the email address

**Trigger:**  
An attacker knows or guesses a user’s email address. The token is:

```python
md5(email + date.today().isoformat())
```

There is no server-side secret, randomness, or stored nonce. The attacker can compute today’s token locally, visit:

```text
/reset?token=<computed>&email=<victim email>
```

and, assuming the reset endpoint checks `check_reset_token(email, token)`, set a new password for the victim.

**Violated goal:**  
Security: password reset must prove control of the user’s email inbox, not merely knowledge of the email address.

**Severity / likelihood:**  
High severity, high likelihood. This is direct account takeover for any known email address. This touches the authentication trust boundary.

**Fix:**  
Use cryptographically random, high-entropy, single-use reset tokens stored server-side as hashes, with expiry. Example shape:

- Generate `token = secrets.token_urlsafe(32)` or equivalent.
- Store `hash(token)`, `user_id`, `created_at`, `expires_at`, `used_at`.
- Email only the raw token.
- On reset, lookup by token hash, require unexpired and unused, then atomically mark used and change password.
- Do not use MD5; token security should come from randomness, not deterministic derivation.

This must block merge.

---

### 2. Reset tokens are reusable for the full day and cannot be revoked independently

**Trigger:**  
A user requests a reset link. Anyone who obtains that link/token can use it repeatedly until the date changes. Even after a successful reset, `check_reset_token` will continue returning true for that email/date because there is no stored token state, no `used_at`, and no per-token invalidation.

**Violated goal:**  
Security and data integrity: a reset credential should be narrowly scoped, expiring, and single-use.

**Severity / likelihood:**  
High severity, medium/high likelihood. Link reuse is common through forwarded emails, shared devices, browser history, email scanners, and logs. Combined with finding 1, this is catastrophic.

**Fix:**  
Same token-store fix as above. Require one-time use and expire tokens after a short window, commonly 15–60 minutes. Invalidate prior outstanding reset tokens when issuing a new one or when password reset succeeds.

---

### 3. Full reset URLs are logged, turning logs into password-reset credentials

```python
log.info(f"sending reset url: {url}")
```

**Trigger:**  
A legitimate user requests a reset. The full URL, including token and email, is written to application logs. Anyone with access to logs, log aggregation, APM breadcrumbs, incident exports, or leaked logs can use the reset link before expiry — and under the current deterministic-token design can also infer/reset more.

**Violated goal:**  
Security/privacy: reset tokens are bearer credentials and must not be exposed outside the intended email channel.

**Severity / likelihood:**  
High severity, medium likelihood. Many engineers/support/vendor systems often have broader log access than production database access. This is a common credential-leak path.

**Fix:**  
Never log reset tokens or full reset URLs. Log only non-sensitive metadata:

```text
password reset email queued user_id=<id> request_id=<id>
```

If debugging delivery is needed, log provider message IDs and delivery status. Redact query strings at ingress/proxy/logging layers too.

---

### 4. Abuse control is not a safe rate limit and can become account lockout

```text
password_reset_count >= 5
```

**Trigger:**  
An attacker repeatedly submits a victim’s email to `/forgot-password`. If the counter is incremented per request, the attacker can exhaust the victim’s lifetime reset allowance and prevent future legitimate resets. The design does not specify a reset window, increment location, decrement/reset behavior, IP/device throttling, CAPTCHA/escalation, or admin recovery path. If the counter is not incremented, the limit does nothing.

**Violated goal:**  
Abuse resistance and user availability: attackers should not be able to lock users out of account recovery, and reset spam should be throttled without permanently harming the account.

**Severity / likelihood:**  
High severity, medium likelihood. This endpoint is unauthenticated and easy to automate. The current scheme either fails open or creates persistent denial of recovery.

**Fix:**  
Replace the permanent account counter with windowed throttles, for example:

- Per-account/email: e.g. max N reset emails per hour/day.
- Per-IP/subnet/device fingerprint: conservative limits.
- Global provider-send limits and alerting.
- Store attempts with timestamps or use a rate-limit service/cache.
- Always return `{"ok": true}` externally, but suppress email sends when limited.
- Add support/admin override and automatic expiry of rate-limit state.

Do not use a lifetime `password_reset_count` as the primary control.

---

## This sprint

### 5. Reset credentials in URL query parameters increase leakage surface

**Trigger:**  
The reset link is:

```text
/reset?token=<token>&email=<email>
```

Query strings can land in browser history, proxy logs, CDN/WAF logs, analytics, crash reports, screenshots, and `Referer` headers if the reset page loads third-party resources or navigates externally.

**Violated goal:**  
Security/privacy: reset credentials should have minimum accidental exposure.

**Severity / likelihood:**  
Medium severity by itself, higher in combination with reusable/day-long tokens. Likelihood is medium.

**Fix:**  

- Prefer a URL containing only an opaque token, not the email.
- Ensure the reset page sends `Referrer-Policy: no-referrer` or at least `same-origin`.
- Avoid third-party resources on reset pages.
- Redact query strings in access logs.
- Keep token expiry short and single-use.

This does not replace the need for server-side random tokens.

---

### 6. Shared notification queue can be abused or degraded during session invalidation — confirm at scale

```python
for s in sessions.for_user(user):
    sessions.revoke(s)
    notifications.enqueue(s.device, "Your password was changed")
```

**Trigger:**  
A user with many active sessions resets their password, or an attacker triggers resets on accounts after compromising/forging reset tokens. The code enqueues one notification per session into the same queue used for product emails, push, and digest jobs. A high-session account, bug, or attack can flood the shared queue and delay unrelated notifications.

**Violated goal:**  
Adjacent-system safety and availability: password reset should not degrade unrelated product notification pipelines.

**Severity / likelihood:**  
Medium severity, likelihood unknown; confirm at scale. Blast radius is broader than auth because the queue is shared.

**Fix:**  

- Put security notifications on a separate queue or priority lane.
- Cap/coalesce notifications: one “password changed” notification per user/event, not per session/device, unless product explicitly requires per-device.
- Make revocation primary and notification best-effort.
- Add queue metrics/alerts and load-test expected worst-case session counts.

---

### 7. URL construction should encode parameters and avoid using raw email as token identity

```python
url = f"https://app.example.com/reset?token={token}&email={e}"
```

**Trigger:**  
If email input contains characters requiring escaping, the generated URL can be malformed or have ambiguous parameters. Even if current emails are validated, this code relies on that invariant indirectly. It also exposes the email address in the reset URL unnecessarily.

**Violated goal:**  
Correctness/privacy: reset links should be unambiguous and avoid unnecessary personal data exposure.

**Severity / likelihood:**  
Low/medium. Lower than the token issues, but easy to fix.

**Fix:**  
Use URL-building helpers with percent-encoding. Ideally include only an opaque reset token in the URL and derive the user from the stored token record.

---

## Backlog / design clarification

### 8. Migration and counter design need rollout clarification if any user-table change remains

```sql
ALTER TABLE users ADD COLUMN password_reset_count INT NOT NULL DEFAULT 0;
```

**Trigger:**  
On some databases/versions and large `users` tables, adding a non-null column with a default can rewrite or lock the table. The document also says “backfill existing users to 0,” but the SQL uses `DEFAULT 0`, so the exact migration strategy is unclear.

**Violated goal:**  
Operability/rollback: auth-adjacent migrations should be predictable and safe.

**Severity / likelihood:**  
Medium or low depending on database/version/table size.

**Fix:**  
If a counter column is still needed, define a safe migration plan for the actual DB engine. But preferably avoid this column and use a separate rate-limit/attempts store with timestamps.

---

## Hypotheses to investigate

- **Timing enumeration:** The handler returns `{"ok": true}` for both existing and non-existing users, which is good, but `users.get_by_email` plus email sending may make response times distinguishable. Consider asynchronous email enqueue and uniform response timing if enumeration risk matters.
- **Reset endpoint details:** The design omits password strength validation, atomic token-consumption/password-change semantics, CSRF/referrer headers, and whether sessions are invalidated transactionally. These should be checked in the implementation/design before merge.
- **Email provider behavior:** Some providers or security scanners prefetch links. Single-use token handling should tolerate link scanning, e.g. only consume token on POST after user submits the new password, not on GET page render.

## OAuth/Auth0 open question

Do not use this feature as the reason to “rip out” all auth right now. That is a separate migration with much larger blast radius. The current design can be made safe incrementally by implementing a standard random, stored, expiring, single-use reset-token flow. However, because homegrown auth is involved, this path should receive stricter security review and tests.

## Summary

The high-level product goal is sound, but the proposed implementation is not safe to merge. The deterministic MD5 token makes account takeover trivial, the no-storage approach prevents single-use revocation, and logging full reset URLs leaks bearer credentials. The abuse limit also needs redesign because it can become either ineffective or a user lockout mechanism.

Reflex vs. verdict: my initial gut was “account takeover via reset-token design,” and the review confirms that as the central blocking risk, with additional blocking issues around token leakage and abuse controls.

**Verdict: unsound.**

The design would move toward **sound-but-needs-these-changes** if it does at least these three things:

1. Replace deterministic MD5 tokens with random, server-stored, hashed, expiring, single-use tokens.
2. Remove reset tokens/full URLs from logs and reduce URL/query leakage.
3. Replace `password_reset_count` with windowed per-account/per-IP rate limiting that cannot permanently lock users out.