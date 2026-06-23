# Adversarial Review: Self-serve Password Reset

## 0. Triage
This touches authentication, session management, and user account security — high blast radius. A bad password reset is one of the highest-impact security failures possible (full account takeover, persistent access, hard to detect). Full adversarial review required.

**Gut reflex:** *The biggest risk is the token generation — it's fundamentally broken in multiple ways that make it trivial to forge.* Let me check that hypothesis.

---

## 1. System Frame

**Goals:**
- Let users self-reset passwords via email
- Reduce support team workload
- Invalidate sessions on password change

**Failure categories:**
- **Security (CRITICAL):** Token forgery, token prediction, token reuse, email interception, rate-limit bypass
- **Data integrity:** Account takeover, session confusion
- **Correctness:** False positives/negatives in validation
- **Reliability:** Email delivery failure, token expiry ambiguity, edge cases (midnight rollover)
- **Maintainability:** Debug-mode logging secrets, no-token-storage pattern vs. auditability
- **Interaction with adjacent systems:** Shared notification queue affects other product emails
- **User impact:** Lockout due to rate limiting (5 per day on a 24h window), no lockout recovery path

**Out of scope:** The OAuth/Auth0 migration question (team's open question — not part of this design)

---

## 2. Steelman

The design prioritizes simplicity and minimal infrastructure. By computing tokens deterministically from email and date, the designers avoid a database table, a database migration for token storage, token expiry cleanup jobs, and any new failure modes from storage. The rate limiting using a simple column prevents brute-force enumeration of tokens or harassment of users. The "don't leak which emails exist" response is a standard security best practice. The sign-out-everywhere loop is comprehensive — it iterates all sessions, revokes each, and sends proactive notifications. The logging to info level seems positioned as a debugging convenience for operational support. The design avoids over-engineering for what was likely scoped as a straightforward feature on a small-to-medium platform.

---

## 3. Blind the Framing

The status "Reviewed and approved by two senior engineers" and the statement "final rubber-stamp before merge" are exactly the kind of approval signals this discipline warns about. I am ignoring them. I am judging only the artifact.

---

## 4. Premortem — It's Shipped and Failed

**Failure 1 (Security — token forgery):** An attacker who discovers the token construction has unlimited, unlogged password resets for any user, any day. `md5(email + date)` is trivially bruteforceable. Since tokens aren't stored, there's no forensic trail of which resets happened. Attacker resets user A's password, takes over account, user A is locked out and has no way to know what happened.

**Failure 2 (Security — token collision/prediction):** A user can predict tomorrow's reset token today. If a user's email is compromised during session A, the attacker can pre-compute the token for tomorrow, and when the rate limit resets at midnight, reset the password without needing any email access.

**Failure 3 (Maintainability / Data leak — log):** The `log.info("sending reset url: {url}")` logs the full URL containing the plaintext token and email to production logs. These logs are accessed by operations, SIEM, and possibly shipped to log aggregation services. An attacker who accesses logs can use these tokens to reset passwords — the tokens are valid until midnight.

**Failure 4 (Reliability — midnight boundary / timezone ambiguity):** `date.today().isoformat()` depends on server timezone. If the server is UTC and the user is in a different timezone, a token created at 11 PM UTC on June 20 becomes invalid at midnight UTC — 5 PM local time on the same day from the user's perspective. This is a subtle and confusing failure for users.

**Failure 5 (Availability — rate limit lockout):** The rate limit is a hard cap of 5 lifetime resets (with a DEFAULT 0 migration for existing users, backfilled to 0). A user who hits this has no path to a reset. If support is required to unblock them, we've reintroduced the manual process the design claims to eliminate — and users are now locked out of their account with zero recourse.

**Failure 6 (Adjacent-system — notification queue congestion):** The sign-out-everywhere code enqueues notifications on the same queue as product emails and digests. A flood of "Your password was changed" notifications (legitimate or from an attack) delays or drops product emails, affecting revenue and user experience. The queue has no isolation.

---

## 5. Turn the Lens on Myself

**What I over-weighted:** I'm probably spending too much energy on the token generation vulnerability because it's the most obvious catastrophic failure. The rate-limit and logging issues are real but lower-impact. I should also check if I'm underweighting the **"no storage"** tradeoff — there is a legitimate simplicity argument, but in this context it's catastrophically wrong.

**What I skipped:** I didn't examine the `invalidate_all_sessions` function closely — the loop over sessions for a user with potentially hundreds of sessions (each device) could be a denial-of-service vector if not paginated or timed out. I also didn't examine whether `notifications.enqueue` is synchronous — if it's synchronous, then the POST to `/forgot-password` blocks on sending N notifications per user, which is a timeout DoS waiting to happen.

**Reconciliation:** The token generation issue is the single finding that alone makes this design unsound. The others (rate-limit, logging, midnight boundary, queue isolation) are this-sprint fixes. I need to be crystal clear about which is blocking.

---

## 6. Ground, Gate, and Rank Findings

### FINDING 1 (BLOCKING): Token generation is trivially forgeable — full account takeover without any user interaction

**(a) Trigger:**
- **Precondition:** Attacker knows a target user's email address (often public, or easily guessed).
- **Step 1:** Attacker calls `make_reset_token(target_email)` locally. MD5 of `target_email + date.today().isoformat()` — zero cryptographic work.
- **Step 2:** Attacker calls `GET /reset?token=<forged_token>&email=<target_email>` or similar endpoint (we have `check_reset_token` that matches exactly this computation).
- **Step 3:** The system validates the token as correct. Attacker sets a new password for the target user.
- **Step 4:** All sessions invalidated; target user is locked out of their own account. Attacker now has full access.
- **Observable bad outcome:** Full account takeover. No forensic trail — the reset isn't logged or stored because no token storage means no "who reset when."

**(b) Violated goal:** The implicit security goal of "only the email account owner can reset the password" is violated. Any other security property (session invalidation, rate limiting) is meaningless once the attacker can forge a valid token at will.

**(c) Severity × Likelihood:** **HIGH severity, HIGH likelihood.** The computation is deterministic, zero-cost to reproduce, and requires no access to the user's email or any user interaction. An attacker can reset every user on the platform in minutes.

**(d) Fix:** **Complete rework.** Use cryptographically-secure random tokens (e.g., `secrets.token_urlsafe(32)`), store them in a new table with expiry, and verify against the stored hash. The "no storage for simplicity" is not viable for a password reset. This is not a fix — it's a redesign.

---

### FINDING 2 (This-sprint): Token URL logged in plaintext to production logs

**(a) Trigger:**
- **Precondition:** Any developer, operator, or SIEM user with log access reads production logs.
- **Step 1:** `log.info(f"sending reset url: {url}")` writes the full URL including the token to logs.
- **Step 2:** Anyone with log access extracts the token, clicks the link, and resets the user's password (before the user does).
- **Observable bad outcome:** Account takeover via log access, which is a much larger attack surface than direct endpoint access.

**(b) Violated goal:** "Don't leak secrets" — a standard security requirement.

**(c) Severity × Likelihood:** **MEDIUM severity, HIGH likelihood.** Severity is lower than finding 1 because it requires log access — but in many organizations, log access is broad. The likelihood is high because the logging is unconditional.

**(d) Fix:** Remove the log line, or log at DEBUG level with a redacted URL (show domain only: `"sending reset for user@example.com"`).

---

### FINDING 3 (This-sprint): Rate limit of 5 total per user is a guaranteed lockout path

**(a) Trigger:**
- **Precondition:** User has used 5 password resets over the lifetime of their account (or a bug/attacker triggers 5 attempts).
- **Step 1:** `password_reset_count >= 5` → reset refused.
- **Step 2:** User clicks "forgot password" — gets `{"ok": True}` (no leak), but no email is sent.
- **Step 3:** User is locked out of their account with no path to recover. Must contact support.
- **Observable bad outcome:** Support burden is preserved (or worsened, because user is angry about a "feature" that locked them out). The design's own stated goal of "support stops doing it manually" is violated.

**(b) Violated goal:** "Let users reset their own password" — the stated goal of the feature.

**(c) Severity × Likelihood:** **MEDIUM severity, MEDIUM likelihood.** It will affect users who change passwords frequently or who have had legitimate password issues. The DEFAULT 0 on existing users backfills all users to zero resets, so existing users can immediately get to 5.

**(d) Fix:** Use a time-windowed rate limit (e.g., "5 per 24 hours") instead of a lifetime count. Reset the counter on a per-day or per-rolling-window basis. OR remove the limit entirely and use CAPTCHA or email-verification-based rate limiting (one reset email per N minutes).

---

### FINDING 4 (Backlog): Midnight boundary / timezone ambiguity

**(a) Trigger:**
- **Precondition:** Server timezone != user's mental timezone. Token created near midnight UTC.
- **Step 1:** User clicks link 6 hours later (local time is still "today" in their timezone; UTC is now "tomorrow").
- **Step 2:** `make_reset_token(email)` recomputes with the new date. Token mismatch. User is told "invalid or expired link."
- **Observable bad outcome:** User cannot reset password; assumes platform is broken; contacts support.

**(b) Violated goal:** Correctness / reliability.

**(c) Severity × Likelihood:** **LOW severity, MEDIUM likelihood** for real-world timezone configurations. This is a user-visible bug but not a security issue.

**(d) Fix:** Use a proper time-windowed approach (e.g., 1 hour expiry) with cryptographically random tokens, and store them. The fix for finding 1 will eliminate this problem naturally.

---

### FINDING 5 (Hypothesis to investigate): Session invalidation blocks on notification queue

**(a) Trigger:**
- **Precondition:** User has N active sessions (e.g., 50+ devices logged in over years).
- **Step 1:** `for s in sessions.for_user(user)` iterates over each session.
- **Step 2:** For each, `notifications.enqueue(...)` is called. If this is synchronous (HTTP call to queue service), the forgot-password POST blocks until all N notifications are enqueued.
- **Step 3:** If N is large (50+), request times out. User gets an error page. Password WAS changed (bad state) but user sees failure.
- **Observable bad outcome:** Confusing UX; the password reset appears to fail but actually succeeded.

**(b) Violated goal:** Reliability / correctness.

**(c) Severity × Likelihood:** **LOW severity, LOW likelihood** — depends on actual session count distributions and whether the queue call is synchronous. This is a hypothesis to investigate, not a finding — I don't have the data.

**(d) Fix:** Make notification enqueuing asynchronous (fire-and-forget or background task). Or paginate the session iteration so the forgot-password endpoint returns quickly and sessions continue to be invalidated asynchronously.

---

### Finding Summary (Ranked):

| Finding | Severity | Action |
|---|---|---|
| Finding 1: Token generation forgeable | CRITICAL (H/H) | **BLOCKING** — redesign required |
| Finding 2: Token logged in plaintext | MEDIUM (M/H) | This-sprint |
| Finding 3: Rate limit creates lockout | MEDIUM (M/M) | This-sprint |
| Finding 4: Midnight boundary bug | LOW (L/M) | Backlog (resolved by finding 1 fix) |
| Finding 5: Session loop blocks on queue | HYPOTHESIS | Investigate |

---

## 7. Verdict: **UNSOUND**

**Gut reflex (from step 1):** "The biggest risk is the token generation."  
**Actual finding:** Token generation is indeed the catastrophic failure — but I also found that the rate limiting creates its own failure of the core goal, and the logging introduces a parallel compromise path. Even fixing only the token generation would leave finding 3 (lockout) and finding 2 (log leak) as problems.

**Verdict:** **Unsound.** This design cannot ship as-is, not even with minor changes. The token generation must be replaced with cryptographically secure tokens stored server-side. Once that is done, the rate limit needs a per-window approach, and all debug logging of tokens must be removed.

**The 1-3 things that would move it to "Sound but needs these changes":**
1. Replace token generation with `secrets.token_urlsafe(32)`, store hashed token in a password_resets table with expiry, verify against stored hash. No deterministic derivation.
2. Remove all token/URL logging from production paths.
3. Change rate limiting from a lifetime cap to a time-windowed limit (e.g., 5 per 24 hours) and reset the counter.

**Open question response:** *"Should we migrate to OAuth/Auth0?"* — Based solely on the quality of this password-reset design, the homegrown auth clearly has security gaps at the design level. Migrating to a battle-tested third-party auth solution would be wise, but it's a separate project. Do NOT use that as a reason to ship this broken design ("we'll replace it all anyway" — classic mistake). Ship a fixed, secure password reset *today*; consider OAuth migration as a separate initiative.