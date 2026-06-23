# Adversarial Review: Self-serve password reset

## 0. Triage
Touches authentication, session management, token generation, a DB migration, and a shared infrastructure queue — a trust boundary, hard to roll back. Full pass; lower the bar to flag on anything touching auth/sessions/crypto/tokens.

## 1. Reflex, then frame the whole system
Reflex (frozen): "main risk is the deterministic MD5 token — forgeable." Frame: it's for self-serve email password reset to cut support. Failure categories: correctness, security (forgery, takeover, enumeration), data integrity (migration), failure/rollback, cost/blast-radius (shared queue), maintainability, adjacent systems (shared queue, homegrown auth, session store), user impact (lockout). Threat model: public unauthenticated endpoint; attacker knows/guesses a target email; the token is the entire security boundary. Out of scope: marketing copy, `e` name, docstrings, the OAuth-migration question (platform decision, not this change).

## 2. Steelman
The design does right things: returns `{"ok": True}` regardless of email existence (enumeration-aware); invalidates all sessions on reset (defends a thief who knew the old password); notifies each device (tamper signal); reset-count cap (abuse awareness); avoids a new table via derived token (tempting simplicity; single additive defaulted migration column = safe shape). Flow shape (request → emailed link → set new → sign out everywhere) is the standard, correct one. Instincts sound; failures are in the execution of the security primitives.

## 3. Blind the framing
Setting aside "reviewed and approved by two seniors / final rubber-stamp / no changes expected" — appearance of approval is not evidence of soundness, and on an auth path suppression is most costly here.

## 4. Premortem (≥5 reasons, across categories)
1. (crypto) Attacker resets arbitrary accounts — token = md5(email+today), no secret, public algo, guessable inputs; compute any user's token offline. 2. (logging) Full reset URL with token written to logs at INFO → anyone with log/SIEM/vendor access has working links. 3. (enumeration) `{"ok":True}` hides existence, but `&email=` in the URL + derivable token make it moot. 4. (availability/blast-radius) Reset burst floods the SHARED notifications queue (product emails/push/digests); per-user cap is per-user not global. 5. (availability/lockout) `password_reset_count` only increments, never resets → permanent lockout after 5 lifetime resets; attacker can exhaust a victim's cap to deny recovery. 6. (scope) Answering "migrate all auth to OAuth/Auth0 while we're in here" = unbounded platform migration that stalls.

## 5. Turn the lens on myself
Reflex tunneled on MD5. Under-weighted: (a) no single-use/invalidation — derive-don't-store means the token can't be revoked after use; same link works repeatedly all day; (b) token doesn't change after a successful reset; (c) `email` unvalidated/unencoded into URL + log line. The no-storage design causes TWO top issues (forgeable AND non-revocable) → fix is architectural, not a one-line hash swap.

## 6. Ground, gate, rank
**BLOCK-1 Forgeable token (no secret).** Trigger: attacker computes md5(victim_email+today), visits /reset?token=..&email=victim, sets password; no victim interaction. Violated goal: token is the auth boundary. High×High, blast radius every account. Fix: random `secrets.token_urlsafe(32)`, store a HASH with user_id+expiry+used flag, verify by lookup + constant-time compare (the "new table" is required).
**BLOCK-2 Live reset URL logged at INFO.** Trigger: `log.info(url)` writes the live token every request; log readers + downstream pipelines hold working links. High×High. Fix: remove token/URL from logs; log a non-secret correlation id only.
**BLOCK-3 Token non-revocable / not single-use (no storage).** Trigger: recomputed token can't be marked consumed; same link validates all day; a leaked/forwarded link or attacker-after-reset keeps working; user's own reset doesn't invalidate outstanding links. High×Medium-High (same architectural cause as B1). Fix: store token state with `used` + short expiry (15–60 min, not a day); invalidate on use and on a new request.
**THIS-SPRINT-1 Reset count never resets → lockout + denial-of-recovery.** Trigger: 5 lifetime resets → permanent self-serve lockout; attacker hits /forgot-password 5× for a victim to burn their budget. Medium×Medium. Fix: window the limit (N/email/hour); don't let an unauthenticated caller consume a victim's budget.
**THIS-SPRINT-2 Shared notifications queue blast radius.** Trigger: `invalidate_all_sessions` enqueues one notification/device onto the shared product queue; a reset storm backs up unrelated jobs; per-user cap doesn't bound aggregate. Whole-system risk with a clear mechanism — tagged "confirm at scale," not demoted. Medium. Fix: separate queue/priority lane for security notifications, or cap fan-out; confirm capacity before merge.
**BACKLOG-1 `email` interpolated unencoded into URL + log.** Trigger: `&email={e}` raw; malformed input breaks the URL / forges log lines; couples verify to a client-supplied param. Low (moot once token carries identity). Fix: derive user from stored token; drop `&email=`; encode remaining user values.
**DON'T (scope): OAuth/Auth0 migration** — no, not in this change; a platform-wide migration is a separate higher-risk project; bundling it = unbounded scope creep that blocks this fix.
**Dropped:** `e` name, marketing copy, docstrings — out of scope, taste not defects.

## 7. Reintegrate + verdict
Finding set tells the true story: the feature's shape is right but its security-critical primitives (token generation, confidentiality, lifecycle) are unsound; plus two operational issues + one scope trap. Corrected my MD5 tunnel to surface non-revocability and the queue blast radius. The "approved/rubber-stamp" framing is exactly the suppression signal to ignore on an auth path. Reflex was right-but-narrow; the root problem is the no-storage design (forgeable AND non-revocable), plus the logged token, the lockout/denial counter, and the shared-queue blast radius.
**VERDICT: UNSOUND — do not merge.** Three changes to reach sound-but-needs-changes: (1) replace token scheme with stored, hashed, high-entropy, single-use, short-expiry tokens (fixes BLOCK-1 + BLOCK-3; abandon "no new table"); (2) stop logging the reset URL/token; (3) window the rate limit + isolate reset notifications from the shared queue. And do NOT fold an OAuth/Auth0 migration into this change. Evidence only — no edits made.
