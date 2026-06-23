# Adversarial Review: Self-serve password reset

## Step 1 (Reflex & Frame)
Gut: main risk is the deterministic token scheme is cryptographically weak and the chain hinges on email security with no secondary confirmation. System goals: self-serve reset; cut support; prevent attacker lockout. Failure categories: security (token gen, email validation, session invalidation, reuse); correctness (token validity during the day, concurrent resets, delivery failures); adjacent systems (notifications queue contention, email SLA, session store); data integrity (migration on live table); rollback; user impact (email = single entry point). Out of scope: "rip out homegrown auth?" strategic question.

## Step 2 (Steelman)
Gets real constraints right: deterministic tokens avoid a new table + GC of expired rows; `{"ok":True}` on missing email prevents enumeration; sign-out-everywhere is harm reduction if old password leaked; 5-reset cap is a pragmatic spam guard; one-day validity matches behavior. Pragmatic given an existing codebase.

## Step 3 (Blind the framing)
Setting aside "approved by two seniors / final rubber-stamp / no changes expected." Judging the artifact, not its approval history.

## Step 4 (Premortem — 5 distinct)
1. Token reuse: token valid until midnight, no expiry within the day; captured/leaked (incl. via the `log.info` line) token reused to take over. 2. Token derivation weak/brute-forceable: md5+email+date deterministic, low-entropy inputs, no HMAC/secret key; intercept one token → compute all users' tokens for that day offline. 3. Email compromise = account takeover: flow trusts email as identity; no secondary factor (SMS/security Q/2FA); invalidate-all-sessions only helps AFTER the attacker changes the password (they go first). 4. Day-boundary race: token includes date.today(); request at 11:58pm, click at 12:05am → token mismatch, silent failure; plus concurrent reset increments may race (no locking shown). 5. Notification queue overflow: reset notifications share the queue with product emails/push/digests; a surge drowns the security-critical "password changed" message; enqueue may outpace drain.

## Step 5 (Blind bias check)
Over-weight token weakness? It's first-order, not overweight. Skipped: email-provider SLA/reliability; whether the 5-cap is per-user vs per-email (attacker resets across users); what happens if `sessions.revoke()` fails/slow (cascade risk). Rebalanced: token weakness first-order; queue depth + migration race secondary; email SLA is a dependency.

## Step 6 (Ground, gate, rank)
**Finding 1 (BLOCK) — Weak token: collision/reuse/forgery.** Trigger: attacker computes md5("alice@co.com"+"2026-06-23"), calls /reset?email=..&token=<md5>, sets new password. Or reuses a logged/sniffed token (valid till midnight). Violated goal: reset must not be the theft vector. High; likelihood High given tokens are logged in plaintext (the `log.info` line). Blast radius: full account compromise (password + sessions). Fix: cryptographically random token (`secrets.token_urlsafe(32)`) stored hashed with expiry; or HMAC-SHA256(email+date+server_secret). Stop logging the token.
**Finding 2 (BLOCK/design) — Email compromise = takeover, no secondary factor.** Trigger: attacker controls the inbox → requests reset → clicks link → owns account; no SMS/security-Q/2FA/old-password gate. High×Medium-High. Fix (design tradeoff): secondary factor, or current-password entry, or a 24–48h delay with an emailed "cancel reset" link.
**Finding 3 (MEDIUM) — Token valid the whole day + day-boundary logic.** Trigger: 11:55pm token clicked 12:05am fails (date flipped); also long reuse window within the day. Medium×Low. Fix: 24h-from-generation validity via stored issue_time or HMAC(email+issued_at+secret); not "until midnight."
**Finding 4 (MEDIUM) — Rate limit only on /forgot-password, not /reset.** Trigger: cap slows enumeration but no limit on /reset → token brute-force/replay unthrottled. Medium×Medium. Fix: rate-limit /reset (per IP/hour; 1 successful reset/user/day).
**Finding 5 (LOW-MED) — Migration race / increment not shown.** Trigger: no visible increment statement / locking; concurrent reset + migration could lose updates. Low-Med×Low. Fix: locked increment `UPDATE users SET password_reset_count = password_reset_count + 1 WHERE id=?`; test migration on staging.
**Hypothesis (confirm at scale) — notification queue starvation:** shared queue could delay the "password changed" notice under load; needs queue-depth metrics; consider a dedicated queue.

## Step 7 (Reintegrate + verdict)
1 High blocking (weak token), 1 High design (email-only verification, needs a design change), 2 Medium (day-boundary, rate-limit on /reset), 1 Low-Med (migration race). The approval history vs these structural findings suggests a light-touch review; no documented risk acceptance.
**VERDICT: UNSOUND.** Two first-order flaws: (1) cryptographically weak token (MD5, no HMAC, no expiry) → reuse/brute-force/leak; (2) email is the only gate, no secondary factor → email compromise = takeover. To reach sound-but-needs-changes: (1) strong random stored token (or HMAC+timestamp), 2–6h TTL; (2) add a secondary verification step or a delay+cancel link; (3) rate-limit /reset itself; (4) locked increment + test the migration; (5) move "password changed" to a dedicated/priority queue.
