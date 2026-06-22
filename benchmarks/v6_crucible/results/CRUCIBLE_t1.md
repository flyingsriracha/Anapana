## Adversarial Review: Self-Serve Password Reset Design

## Step 0. Triage
Multi-system, hard-to-roll-back change touching a trust boundary (authentication). Affects session management, email delivery, rate limiting, and a DB migration. Full pass required.

## Step 1. Reflex, then frame the whole system
**Gut reflex:** main risk is the token generation algorithm — deterministic MD5 over email + date is broken-by-design.
**Goals:** user self-reset via email; stop manual support; kick out attacker who had old password.
**Failure categories:** security/trust boundary (forgery, theft, replay, enumeration, sessions); correctness; data integrity (migration, race); performance (abuse at scale, queue saturation); failure/rollback (email fail? migration break?); interaction with adjacent systems (shared notifications queue, email provider); user impact (usability, timing edges).
Threat model: attacker who knows/guesses a target email; also a legit user hitting edges. Auth is homegrown, no external backstop. Out of scope per the doc: full OAuth migration, email copy, docstrings.

## Step 2. Steelman
Core premise sound: email-verified reset is standard; no-storage eliminates stale-token cleanup/collision bugs; sign-out-everywhere is good hygiene, scoped to a successful reset; rate limiter is a simple non-bypassable counter; migration is minimal/reversible; non-disclosure of unknown emails on forgot-password is correctly implemented. Reasonable skeleton against a real support-cost problem.

## Step 3. Blind the framing
Setting aside "reviewed and approved by two senior engineers," "final rubber-stamp," "we don't expect changes" — a suppression signal, not evidence of soundness.

## Step 4. Premortem — across categories
1. **Token forgery (security):** attacker computes `md5(victim_email + date.today())` in ms; both inputs public; no secret. Silent password reset without victim initiating.
2. **Token valid window 0–24h at day boundaries (correctness/security):** "valid for the day" is wrong; validity is 0–24h depending on time of request; midnight rollover silently breaks the user's link.
3. **Full reset URL logged at INFO (security):** `log.info` writes the live credential to logs (Splunk/Datadog/S3, SREs, third parties). Anyone with log read access resets any account during the window.
4. **Rate limiter per-user, never resets (user impact/correctness):** increments only; no decay/reset; legit user locked out after 5 lifetime resets; counter doesn't count failed verifications, so an attacker computing the token directly never touches it.
5. **Shared notifications queue as blast-radius amplifier (adjacent systems/perf):** one enqueue per revoked session into the same queue as product emails/push/digests; many sessions or a burst could starve product notifications; partial-failure semantics between revoke and enqueue unclear.

## Step 5. Turn the lens on myself
Over-weighted token (warranted). Under-weighted: migration `ALTER TABLE ... NOT NULL DEFAULT` can be a full-table rewrite/lock on large tables (medium, infra-dependent); timing oracle on unknown emails (minor, hypothesis); no token invalidation after first use (significant — stateless = nothing to consume). Reconciled below.

## Step 6. Ground, gate, and rank
### BLOCK
**B1 Token fully forgeable — no secret.** Trigger: know email → compute md5(email+today) → POST /reset → set password; no victim interaction. Violated goal: only the user should reset their own password. Severity×likelihood: High×High; blast radius every account. Fix: random token `secrets.token_urlsafe(32)` stored server-side (`token_hash,user_id,expires_at,used_at`), 15–60 min expiry, single-use.
**B2 Live reset URL in logs.** Trigger: `log.info(url)` every request; log readers extract token+email. High×High. Fix: remove; log only `user_id`.
**B3 No token invalidation after use.** Trigger: stateless → nothing marks consumed; a leaked token (B2/forwarding/history) reused within the day. High×Medium. Fix: server-side `used_at`, reject if set.
### THIS-SPRINT
**T1 Rate limiter never resets — legit lockout.** Trigger: 5 lifetime resets → permanent lockout → back to manual support (defeats the goal). Medium×Medium. Fix: reset on success; rolling window (5/24h); document the cap path.
**T2 Token window 0–24h not "the day."** Trigger: request at 23:59, click at 00:01 → invalid; confusion. Medium×Medium. Fix: server-side `expires_at = now()+30min`.
### BACKLOG
**BL1 ALTER TABLE may lock large tables.** Medium×Low-Medium (engine/size dependent). Fix: nullable + app-side default, or separate table, or online schema change.
### HYPOTHESIS
**H1 Timing oracle on unknown emails** (needs measurement). **H2 Notifications queue saturation / partial-failure** (needs throughput + transactional check).

## Step 7. Reintegrate and verdict
Findings span security (B1–B3), user impact (T1), correctness (T2), availability (BL1); no single category dominates; adjacency risk flagged at hypothesis where evidence is uncertain. Reflex (token) was correct but incomplete — B2 (log leak) is independently catastrophic and higher-likelihood in practice.
**Verdict: UNSOUND.** Complete auth bypass (B1) + credential-in-logs (B2) + reuse (B3). Three changes to reach "sound-but-needs-changes": (1) random server-side token w/ expiry+used-at; (2) remove the URL log line; (3) reset the counter on success + windowed policy. The "approved" framing is set aside — the prior review missed textbook auth vulns.
