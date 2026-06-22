## Adversarial Review: Self-serve password reset design

## 0. Triage
Touches authentication, email, token generation, session management, and a DB migration. Multi-system, hard to partially roll back, sits on a trust boundary (account takeover is the blast radius). Full pass.

## 1. Reflex, then frame the whole system
**Gut reflex:** token generation looks cryptographically wrong — catastrophic path.
**Goals:** self-reset without support; prevent account takeover during reset; don't leak which emails exist; rate-limit abuse; sign out compromised sessions.
**Failure categories:** security/trust boundary; correctness; data integrity (migration, race); performance (N+1, queue saturation); failure/rollback; cost/operational (log leakage, abuse); interaction with adjacent systems (shared notifications queue); user impact (UX, token expiry edges).
Out of scope per the doc: OAuth/Auth0 migration.

## 2. Steelman
Genuinely good calls: email-enumeration protection (`{"ok": True}` regardless) is correct and deliberate; sign-out-all-sessions on reset is sound hygiene; migration `DEFAULT 0` is backward-compatible; the rate-limit concept addresses real abuse; deterministic no-table token is a real complexity reduction and the author flags the tradeoff. The design does not ignore security — it has one load-bearing cryptographic piece that's wrong in a way that negates much of the rest.

## 3. Blind the framing
"Reviewed and approved by two senior engineers," "final rubber-stamp" — noted and set aside. The artifact gets reviewed, not its approval history.

## 4. Premortem — across categories
A. **Token trivially forgeable (security/correctness).** `MD5(email + date)` — no secret, not a MAC. Attacker who knows the email computes today's token offline; `/reset?token=<md5>&email=victim` → takeover, no prior interaction.
B. **Reset URL + email logged in plaintext (security/operational).** `log.info(url)` → aggregators, 30–90d retention, broad eng access; any log reader gets a live reset link. Independent second path to takeover.
C. **Rate limit resets nothing and is permanently sticky (correctness/user impact).** `password_reset_count` increments, never decremented/cleared; legit user locked out after 5 lifetime resets; per-user not per-IP, so a network attacker hits the endpoint 5× to permanently lock a target out — DoS against legit users.
D. **Shared notifications queue couples reset to product/digest load (perf/failure).** Same queue as product emails/push/digests; saturation delays sign-out notifications; transactionality of `sessions.revoke` vs `notifications.enqueue` unclear (partial failure).
E. **Token valid all day, no per-use invalidation (security).** Stateless → clicking doesn't consume it; valid the whole UTC day for anyone holding it (compounds B). UTC-midnight edge: request 11:58pm, click 3 min later → `date.today()` rolled → link silently broken.

## 5. Turn the lens on myself
Over-weighted token (correct). Checked under-weighting: migration `NOT NULL DEFAULT 0` is usually fine on modern Postgres but may lock large MySQL tables — a "hypothesis to investigate," not asserted. Enumeration protection is correctly implemented (no false finding). Premortem spans security (A,B,E), correctness/UX (C), perf/failure (D) — broad enough. D is real but lower severity than A,B,C,E → rank lower. Rollback-on-email-failure is a gap → hypothesis.

## 6. Ground, gate, and rank
**FINDING 1 — Token trivially forgeable.** Trigger: compute `md5("victim@example.com"+"2026-06-22")`, visit `/reset?token=…&email=victim` → `check_reset_token` True → set password; no prior server interaction. Violated goal: prevent unauthorized takeover. Severity×likelihood **High×High**; blast radius full takeover for any user with a known email. Fix: `secrets.token_urlsafe(32)` stored w/ expiry + single-use, OR HMAC(SECRET_KEY, email+date) with a server secret. **BLOCK.**
**FINDING 2 — Reset URL logged plaintext.** Trigger: `log.info(url)` on every request → log readers extract token+email → reset within the day. **High×High.** Fix: log only `user_id`; never token/URL. **BLOCK.**
**FINDING 3 — Rate limit sticky-forever + DoS vector.** Lockout path: 5 lifetime resets → permanent lockout → back to manual support. DoS path: attacker calls `/forgot-password` 5× on a target email → target can never self-reset. **High×Medium.** Fix: reset on success; time-windowed counter; per-IP primary. **BLOCK** (DoS + permanent lockout).
**FINDING 4 — No token invalidation after use.** Trigger: reset done, same link still valid all day; if also in logs, a later log reader reuses it; UTC-midnight breakage too. **High×High** combined with #2; **Medium×Medium** standalone. Fix: stateful used-flag / nonce; test midnight edge. **THIS-SPRINT** (escalates to BLOCK if #1 fixed statelessly and #2 unfixed).
**FINDING 5 (lower) — Shared notifications queue coupling.** Trigger: digest/campaign saturates shared queue; loop partial failure → some sessions revoked, some devices not notified; no retry. **Medium×Low** (revokes are DB writes separate from the queue → devices unnotified, not still-logged-in). Fix: revoke transactionally first, then enqueue; dedicated/priority lane for security notifications. **THIS-SPRINT.**
**HYPOTHESIS — migration table lock** on large MySQL/MariaDB; engine/row-count dependent. Investigate before deploying.

## 7. Reintegrate and verdict
Three independent BLOCK findings, all on the trust boundary but with distinct failure paths (token construction / log hygiene / rate-limit) — fixing one doesn't fix the others. #4 sharpens with the rest; #5 is operational hygiene. Not fixated on one threat — items span token crypto, logs, rate-limit, lifecycle, queue. Reflex (token) was right but incomplete (missed the log + rate-limit blockers).
**VERDICT: UNSOUND.** Three blockers before merge: (1) replace MD5 token with secure server-secret/stateful token; (2) remove/redact the URL log line; (3) fix the rate-limit (reset on success; windowed; per-IP). The "approved/rubber-stamp" framing did not change this — the crypto flaw needs adversarial thinking to surface, not syntactic review.
