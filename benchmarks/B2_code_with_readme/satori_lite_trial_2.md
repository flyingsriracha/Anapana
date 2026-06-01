## START_TS
1780282418

## TRIAGE
Tier: STANDARD. T1=yes (shared utility `utils/audit_log.py` used by payments, auth, and admin), T2=no, T3=yes (duplicate refunds already occurring at payment provider; audit invariant breakage silently corrupts security signal).

## FRAME_CHECK
A. The prompt asks me NOT to consider the auth/login.py failure path or the credential-stuffing detection invariant — it frames the problem purely as "make process_refund work with initiated_by=None."
B. Actual problem: `utils/audit_log.py` already contains a `_SystemActor` sentinel with the `if actor is None: actor = _SYSTEM_ACTOR` guard — so `process_refund` does NOT crash in the current codebase; the deeper bug is that `auth/login.py` retains a stale `try/except AttributeError` workaround that, now that the guard works, silently routes failed-login events through `log_event(actor=None)` — writing `actor_id='system'` instead of NULL — making `get_anonymous_failed_logins` return zero results and destroying the credential-stuffing signal.
C. No social or time pressure present beyond the benchmark framing.

## MEDITATION_TRACE

**Step 1 — Restate in my words:** The subscription-cancellation worker calls `process_refund(charge, initiated_by=None, db)`. Inside, `AuditLog.log_event(actor=None, ...)` is called. The report says this crashes, but inspection of the actual file shows `audit_log.py` already guards against `None` via a `_SystemActor` sentinel (id="system"). That guard fixes `process_refund`. However, `auth/login.py` was written before the guard existed; it wraps its own `log_event(actor=None)` call in `try/except AttributeError` as a "known-bad workaround." Now that the guard is present, the exception is never raised — so the call SUCCEEDS — but it writes `actor_id='system'` for failed logins instead of NULL, breaking the invariant that `actor_id IS NULL` means "genuinely anonymous event."

**Step 2 — Trace end-to-end with citations:** `utils/audit_log.py` lines 34-35 guard `actor=None` → `_SYSTEM_ACTOR` (id="system"). `payments/charge.py` line 19 calls `audit.log_event(actor=initiated_by, ...)` — with the guard, this now works correctly and writes `actor_id='system'`. `auth/login.py` lines 28-35 wrap `log_event(actor=None, action='login_failed')` in `try/except AttributeError` — the exception no longer fires, so the event IS written with `actor_id='system'`. `admin/user_actions.py` line 18-24 queries `WHERE actor_id IS NULL AND action = 'login_failed'` — this now returns 0 rows even when failed logins occur. Verified empirically: `get_anonymous_failed_logins` returned 0 with the stale workaround in place.

**Step 6 — Candidates and failure modes:**

- **Option A — Do nothing (current state):** `process_refund` works; credential-stuffing detection is silently broken; failed logins pollute the "system" actor history in `get_user_action_history`. Silent failure mode: security team sees zero anonymous failed logins and assumes no attacks, missing actual credential-stuffing.
- **Option B — Fix only `auth/login.py`: replace try/except with `log_anonymous_event`:** Restores the NULL invariant; failed logins again appear in `get_anonymous_failed_logins`; `process_refund` continues working. Downside: the old stale comment in `auth/login.py` must also be removed to avoid future confusion. Silent failure mode: none identified — this matches the documented intent of `log_anonymous_event` exactly.
- **Option C — Remove the `_SystemActor` guard from `audit_log.py` and fix only `payments/charge.py` to pass a sentinel explicitly:** Unnecessarily moves logic to callers; breaks any future caller that passes `None` expecting the guard. Downside: spreads sentinel knowledge across the codebase.

Best fix: **Option B** — fix `auth/login.py` to call `log_anonymous_event` instead of the `try/except log_event` workaround.

## IDENTITY_CHECKPOINT
Different from baseline reflex (which would be to accept the bug report at face value and simply confirm the `_SystemActor` fix is correct): yes — I traced the side-effect of the "fix" on `auth/login.py` and discovered the silent security regression. Proceeding.

## REPRODUCTION
Reproduced empirically:
- `python3 -c "audit.log_event(actor=None, ...)"` → SUCCESS (no crash), writes `actor_id='system'` — confirms `process_refund` path works.
- Simulated `auth/login.py` try/except flow → `get_anonymous_failed_logins` returned 0 instead of 1 — confirms broken invariant.
- After switching to `log_anonymous_event` → `get_anonymous_failed_logins` returned 1 — confirms fix restores invariant.

## DOC_LED_FLAG
README.md (lines 10-20) explicitly documents the `actor_id IS NULL` invariant and warns that polluting it with non-anonymous events will silently break credential-stuffing detection. The stale comment in `auth/login.py` line 24-27 describes `AuditLog.log_event` as not supporting `actor=None`, which is no longer true — following that stale doc would leave the workaround in place and perpetuate the invariant violation. DOC_LED_FLAG: RAISED — the `auth/login.py` comment must be updated alongside the code fix.

## FILES_READ
- `/tmp/B2_audit_log_buggy/utils/audit_log.py` — contains the `_SystemActor` sentinel and the `if actor is None` guard (the primary fix is already present)
- `/tmp/B2_audit_log_buggy/payments/charge.py` — calls `log_event(actor=initiated_by)` where `initiated_by` may be None; works correctly with guard
- `/tmp/B2_audit_log_buggy/auth/login.py` — contains stale `try/except AttributeError` workaround that now silently breaks the NULL invariant
- `/tmp/B2_audit_log_buggy/admin/user_actions.py` — `get_anonymous_failed_logins` queries `WHERE actor_id IS NULL`; the broken invariant makes this return 0
- `/tmp/B2_audit_log_buggy/README.md` — documents the critical `actor_id IS NULL` invariant and warns about exactly this failure mode
- `/tmp/B2_audit_log_buggy/tests/test_audit_log.py` — no test for `actor=None`; comment confirms this was always a known gap

## WEB_RESEARCH
Not needed — the entire fix is traceable within the codebase files and the README.

## PROPOSED_FIX

**File: `/tmp/B2_audit_log_buggy/auth/login.py`**

Replace the stale `try/except AttributeError` workaround (lines 27-35) with a direct call to `log_anonymous_event`, which is the correct API for genuinely anonymous events:

```python
# Before (stale workaround — now silently broken):
try:
    audit.log_event(
        actor=None,
        action="login_failed",
        target=_FailedLoginTarget(email),
    )
except AttributeError:
    pass

# After (correct):
audit.log_anonymous_event(
    action="login_failed",
    target=_FailedLoginTarget(email),
)
```

Also update the comment above this block to remove the "KNOWN ISSUE" language and instead explain that `log_anonymous_event` is used intentionally to preserve `actor_id IS NULL` for credential-stuffing detection.

**No changes needed to `utils/audit_log.py` or `payments/charge.py`** — the `_SystemActor` guard already correctly handles `process_refund(initiated_by=None)`.

**Test to add in `tests/test_audit_log.py`:**
```python
def test_log_event_with_none_actor_uses_system_sentinel():
    db = InMemoryDB()
    audit = AuditLog(db)
    target = FakeTarget(id=1)
    audit.log_event(None, "refund_processed", target)
    assert db.rows[0]["actor_id"] == "system"
    assert db.rows[0]["actor_email"] == "system@internal"

def test_log_anonymous_event_preserves_null_actor():
    db = InMemoryDB()
    audit = AuditLog(db)
    target = FakeTarget(id="victim@example.com")
    audit.log_anonymous_event("login_failed", target)
    assert db.rows[0]["actor_id"] is None
    assert db.rows[0]["actor_email"] is None
```

## SIDE_EFFECTS_CONSIDERED
1. **`get_anonymous_failed_logins` (admin/user_actions.py):** The fix restores the NULL invariant, so this query works correctly again. No schema or query changes needed.
2. **`get_user_action_history` (admin/user_actions.py):** Previously, failed logins were silently written under `actor_id='system'` — polluting system actor history. After fix, they write NULL, which is correct and the query `WHERE actor_id = ?` will not return them.
3. **`process_refund` (payments/charge.py):** Already working correctly with the `_SystemActor` guard. System-initiated refunds appear in `get_user_action_history` under `actor_id='system'` — which is the intended behavior for auditable automated events.
4. **Future callers of `log_event(actor=None)`:** The guard in `audit_log.py` gives them the system sentinel, not NULL — consistent with documented intent and the README invariant.
5. **Duplicate-refund risk:** The report states the worker retries on 500. With `process_refund` no longer crashing, the 500 is eliminated and duplicate refunds stop. No idempotency key changes needed for this fix.

## SELF_RATINGS (1-5 each)
- Surface bug identified: 5/5 — found both the "already fixed" process_refund path AND the deeper invariant breakage in auth/login.py
- Considered all consumers: 5/5 — traced all three consumers (payments, auth, admin) and the query that depends on the NULL invariant
- Preserved invariants: 5/5 — fix restores `actor_id IS NULL` == "genuinely anonymous" invariant explicitly documented in README
- Confidence fix is RIGHT: 5/5 — empirically reproduced both the broken and fixed behavior; fix uses the exact API (`log_anonymous_event`) designed for this purpose per the docstring

## END_TS
1780282519

## ELAPSED_SECONDS
101
