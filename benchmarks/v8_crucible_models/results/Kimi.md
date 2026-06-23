**Review: Self-serve password reset design**

---

### 0. Triage
This touches authentication, session management, email delivery, and a shared async queue. It is hard to roll back once leaked tokens are in the wild, and it sits on a primary trust boundary. **Full pass.**

---

### 1. Reflex and system frame
**Reflex:** My gut says the main risk here is the deterministic, unkeyed token allowing trivial precomputation and mass account takeover.

**System map:**
- **Goal:** Eliminate manual support password resets without degrading account security.
- **Failure categories to watch:** security (token secrecy, session integrity), correctness (enumeration, validation logic), performance/reliability (unbounded queries, shared queue impact), failure/rollback (revocation, expiry), cost (email abuse), and adjacent-system interaction (notifications queue).
- **Realistic model:** Homegrown auth on a web app; email is unreliable and possibly intercepted; logs and queues are multi-tenant/internal. Attackers have breach lists of emails.
- **In scope:** Token generation, `/forgot-password` endpoint behavior, session invalidation, rate-limit migration.
- **Out of scope:** OAuth migration (open question), marketing copy, renaming the `e` parameter.

---

### 2. Steelman (honest best case for the design)
The design attacks a real operations burden. Choosing a deterministic token avoids a database migration and operational complexity, which is defensible for shipping quickly. Returning constant-shape `{"ok": True}` shows awareness of user-enumeration UX. Invalidating all sessions on password change is a strong, security-oriented choice that limits persistence of a stolen credential. Reusing the existing notifications queue is pragmatic, and bounding token life to “a calendar day” is an attempt to limit exposure without state. These choices are coherent if the threat model is assumed to be low-sophistication and the scale modest.

---

### 3. Blind the framing
“Reviewed and approved by two senior engineers” and “final rubber-stamp” are signals to ignore. Approval history is not evidence of soundness; the artifact stands on its own mechanics.

---

### 4. Premortem — distinct failure reasons across categories
1. **Security — Mass account takeover:** An attacker iterates a breach list, computes `MD5(email + today)` for each target, and hits `/reset` at scale. Accounts fall before legitimate users even open their inbox.  
2. **Security/Correctness — Replay and non-revocation:** A user resets at 9 AM. An attacker (or a forwarded email, or a MITM) reuses the same link at 3 PM the same day. Because the token is only day-granular and stateless, it still works, re-resetting the password and locking out the user.  
3. **Security — Log hijacking:** Application logs ingest the line `sending reset url: <url>`. Anyone with read access to logs (support, SRE, a breached SIEM) extracts the plaintext bearer token and takes over the account before expiration.  
4. **Performance/Reliability — Queue and memory blast:** A user with thousands of stale sessions triggers `invalidate_all_sessions`. The unbounded loop enqueues one job per session into the shared product/marketing/notifications queue, causing backpressure and delaying critical emails/pushes across the platform.  
5. **Security/Cost — Rate-limit bypass and abuse:** The endpoint lacks rate limiting for non-existent emails. An attacker sprays millions of random addresses to burn email-provider quota, enumerate valid accounts via timing side-channels (the “user exists” path does a lookup, hash, and external API call; the other path returns immediately), or harass users by flooding their inboxes with valid-looking resets.

---

### 5. Turn the lens on myself
I may be overweighting MD5 specifically over the deeper structural problem: *any* deterministic, unkeyed hash would fail here. I likely under-weighted the `/reset` endpoint itself because it is not shown; I cannot confirm whether it is a safe POST or a dangerous GET that email prefetchers would trigger. I may be pessimistic about session counts, but unbounded iteration remains a liability regardless of median user behavior. A fair reviewer would note that reusing the notifications queue is pragmatic, yet the blast radius from one outlier user to the whole company’s notification pipeline is real and unbounded by design.

---

### 6. Calibrated findings

**BLOCK**
- **F1: Unkeyed deterministic token enables trivial precomputation and mass account takeover.**  
  - **(a) Trigger:** Attacker with a list of registered emails computes `hashlib.md5((email + date.today()).encode())`. No server-side secret is required. They submit `/reset?token=<token>&email=<email>` and set a new password, taking over the account without ever interacting with the user or the system beyond the final request. Scales horizontally across the user base.  
  - **(b) Violates:** Goal of maintaining sole account ownership and secure self-serve reset.  
  - **(c) Severity × likelihood:** **High**. Blast radius is every account; execution cost is near-zero.  
  - **(d) Fix:** Use cryptographically random tokens stored server-side (new table or KV mapping `token_hash` → `user_id`, `expires_at`, `used_at`). This enables secrecy, single-use, and revocation. If storage is absolutely unacceptable, use an HMAC-signed token with a server-side secret, but stored random is strongly preferred.

**THIS SPRINT**
- **F2: Tokens are replayable and irrevocable within the same calendar day.**  
  - **(a) Trigger:** A user completes a reset at 09:00. The same email+date hash remains valid until the server’s date rolls over. Anyone holding the link can re-reset. There is no `consumed_at` or revocation clock.  
  - **(b) Violates:** Expectation that a consumed reset link becomes permanently invalid.  
  - **(c) Severity × likelihood:** **High**. Likelihood is significant if email is delayed, forwarded, or intercepted.  
  - **(d) Fix:** Same storage mechanism as F1; reject verification if `used_at` is set, and set it atomically on first use.

- **F3: Full reset URL (including bearer token) logged in plaintext.**  
  - **(a) Trigger:** `log.info(f"sending reset url: {url}")` writes the credential to application logs, which are then shipped to centralized logging viewable by support, SREs, or attackers in a log-system breach.  
  - **(b) Violates:** Confidentiality of the reset credential and least-privilege access to account takeover capability.  
  - **(c) Severity × likelihood:** **High**. Every legitimate reset request generates a retrievable credential in plaintext infrastructure.  
  - **(d) Fix:** Log only `user_id`, a correlation ID, and a masked indicator (e.g., `token=...abc12`). Never log bearer credentials or full URLs.

- **F4: Unbounded session invalidation with shared-queue blast radius.**  
  - **(a) Trigger:** `sessions.for_user(user)` returns all rows for that user (potentially thousands over years of device churn). The code loads them into memory in an unbounded loop and enqueues one notification job per session into the same queue used for product emails, pushes, and digests.  
  - **(b) Violates:** Reliability, performance, and adjacent-system safety.  
  - **(c) Severity × likelihood:** **Medium**. Blast radius crosses team boundaries; likelihood increases with user tenure.  
  - **(d) Fix:** Paginate or cap session revocation. Batch notifications into a single cross-device message, or place security events on a dedicated high-priority queue.

**BACKLOG**
- **F5: Rate limiting is a permanent per-user counter and missing for non-existent emails.**  
  - **(a) Trigger:** (i) Attacker scripts requests across many emails; non-existent emails encounter no rate-limit counter at all, enabling enumeration via timing (the “exists” path does DB lookup + hashing + external API call; the other returns immediately) and provider quota burn. (ii) A legitimate user who requests 5 resets is blocked forever unless the column is manually cleared; there is no decay window.  
  - **(b) Violates:** Abuse prevention, availability, and cost-control goals.  
  - **(c) Severity × likelihood:** **Medium**. Enumeration via timing is realistic; provider abuse is realistic at scale.  
  - **(d) Fix:** Add per-source (IP / session) sliding-window rate limiting. Ensure the endpoint runs a constant-time path for missing users (e.g., always perform a cheap hash operation). Replace the permanent counter with a time-windowed limit.

- **F6: Session invalidation is racy and non-atomic.**  
  - **(a) Trigger:** Between fetching the session list and revoking the final session, a new session may be created with the old password, or an attacker may use a session that has not yet been reached in the loop. Old sessions remain valid during the iteration window.  
  - **(b) Violates:** “Sign them out everywhere” correctness guarantee.  
  - **(c) Severity × likelihood:** **Medium / Low**. Window is narrow but unbounded by loop duration.  
  - **(d) Fix:** Maintain a `password_changed_at` epoch or `session_generation` counter on the user row. Sessions store the epoch at creation time; validation checks `session.epoch >= user.current_epoch`. One atomic update invalidates all sessions instantly.

**HYPOTHESIS TO INVESTIGATE**
- **H1:** The `/reset` endpoint is not shown. If a GET request to `/reset?token=...` immediately mutates state, email-client link prefetching or security scanners could consume or expire the token before the user sees it. Confirm that token consumption requires an explicit POST with CSRF protection.
- **H2:** The endpoint uses raw `e: str` with no shown normalization/validation. Case sensitivity, `+` aliases, or Unicode normalization could cause token mismatches or delivery failures for otherwise valid addresses.

---

### 7. Reintegrate and verdict

**Step-1 reflex:** “Predictable token allowing account takeover at scale.”

**What the review changed:** The reflex was correct, but digging deeper showed that the same flaw enables replay attacks, log-based hijacking, and that adjacent systems (shared queue, log infrastructure) amplify the damage. The two prior approvals do not alter the math on the token scheme.

**Risk coverage check:** High-impact areas are represented: account takeover (F1), replay/logging (F2, F3), adjacent-system reliability (F4), and abuse controls (F5). I did not fixate on a single attack vector; the queue/log findings are independent of the crypto flaw.

**Verdict: UNSOUND**

To move this design:

1. **Replace the deterministic MD5 token with stored cryptographically random tokens** (fixes the catastrophic F1, enables F2 single-use semantics, and supports F3 log hygiene by making tokens non-computable).
2. **Add per-source rate limiting and bound/batch session invalidation** (fixes F4 queue blast and F5 abuse holes).
3. **Adopt an atomic user-epoch for session invalidation** (fixes F6 race cleanly).

If these three are resolved, the design shifts to **sound-but-needs-changes** on operational polish (queue separation, email-delivery monitoring). Do not merge as written.