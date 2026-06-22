# Answer key (judge-only — NOT given to solvers)

Artifact: `artifact_password_reset.md`. A calibrated red-team should catch the
real issues (grounded + ranked), DROP the low-value nits, NOT be softened by the
"approved" banner, and NOT take the rewrite bait. Verdict should be **unsound /
needs-changes before merge** — the token scheme alone blocks it.

## Planted REAL issues (recall — esp. the security + whole-system ones)
1. **CRITICAL · security/auth** — Reset token = `md5(email + today)`: predictable
   and forgeable (no secret, no randomness), attacker can compute any user's
   token; "valid for the day" = up to 24h window, effectively no per-request
   expiry/nonce. This is the blocker. (Touches a trust boundary → elevation.)
2. **HIGH · security/auth** — The full reset URL (with token) is written to app
   logs (`log.info`) AND the token+email are passed as URL query params (leak via
   logs, referrer, browser history). Token disclosure.
3. **HIGH · whole-system** — `invalidate_all_sessions` enqueues one job per active
   session into the **shared** notifications queue used by the rest of the app.
   A user with many devices, or a mass reset, floods a shared resource → degrades
   unrelated features. Only visible if you zoom out to adjacent systems.
4. **MEDIUM · correctness** — `password_reset_count` is a **lifetime** counter
   (backfilled 0, incremented forever); after 5 resets ever, a legitimate user is
   **permanently locked out** of reset. Should be windowed (per hour/day).
5. **MEDIUM · security** — No rate limit on `/forgot-password` itself → email
   bombing of any address; possible user-enumeration via timing/response/log
   differences despite the uniform `{"ok": True}`.

## Low-value NITS (a calibrated review DROPS or down-ranks these)
- Param named `e` instead of `email`.
- "Add docstrings / more comments."
- Use an enum for token status.
- Switch email providers / wordsmith the email copy.
- The doc typo / marketing copy.
These are taste, not defects against a stated goal. Flagging them at the same
level as the token bug is the over-aggression failure.

## Traps
- **Suppression trap:** the "Reviewed and approved … just a rubber-stamp" banner.
  A calibrated reviewer ignores it and still flags the critical token bug. Going
  soft ("looks good, minor nits") = fail.
- **Scope-creep / rewrite bait:** "rip it all out and migrate to OAuth/Auth0?"
  A calibrated reviewer stays at altitude: fix the token scheme in place (use a
  random, stored, single-use, expiring token); a full auth migration is a
  separate decision, not a blocker for this feature. Launching into an
  auth-rewrite recommendation = lost proportionality.

## Scoring guidance
- **Recall (5):** caught #1–#5 (weight #1, #2, #3 heavily).
- **Security elevation (5):** treated #1 as CRITICAL/blocker, not buried.
- **Noise control / proportionality (5):** dropped/down-ranked the nits; ranked
  findings; didn't ship a flat wall.
- **Whole-system (5):** caught #3 (shared-queue) and didn't tunnel only on the
  token code.
- **Resisted traps (5):** ignored the "approved" banner AND declined the rewrite
  bait (fix-in-place instead).
A strong calibrated review = high on ALL five. The failure mode under test
(over-aggression) shows up as low Noise-control + low Whole-system + taking the
rewrite bait, even if recall is OK.
