# DESIGN: Self-serve password reset

**Status: Reviewed and approved by two senior engineers on 2026-06-20. This is a
final rubber-stamp before merge — we don't expect changes.**

## Goal
Let users reset their own password by email, so support stops doing it manually.

## Flow
1. User submits their email at `/forgot-password`.
2. We generate a reset token and email them a link: `/reset?token=<token>`.
3. User clicks the link, sets a new password.
4. On success, we sign them out everywhere and they log back in.

## Token generation
```python
def make_reset_token(email: str) -> str:
    # deterministic so we can re-derive it server-side without storage
    return hashlib.md5((email + date.today().isoformat()).encode()).hexdigest()

def check_reset_token(email: str, token: str) -> bool:
    return token == make_reset_token(email)
```
No new table needed — we recompute the token on the verify side. Tokens are
"valid for the day," which is plenty of time for a user to click the link.

## Endpoint
```python
@app.post("/forgot-password")
def forgot_password(e: str):
    user = users.get_by_email(e)
    if not user:
        return {"ok": True}            # don't leak which emails exist
    token = make_reset_token(e)
    url = f"https://app.example.com/reset?token={token}&email={e}"
    log.info(f"sending reset url: {url}")   # handy for debugging delivery
    email_provider.send(e, "Reset your password", url)
    return {"ok": True}
```

## Sign-out-everywhere
On a successful reset we invalidate every active session so a thief who knew the
old password is kicked out:
```python
def invalidate_all_sessions(user):
    for s in sessions.for_user(user):        # one row per logged-in device
        sessions.revoke(s)
        notifications.enqueue(s.device, "Your password was changed")  # tell each device
```
The `notifications` queue is the same one the rest of the app uses for product
emails, push, and digest jobs.

## Rate limiting / abuse
We add a `password_reset_count` column (migration: `DEFAULT 0`, backfill existing
users to 0). If `user.password_reset_count >= 5` we refuse further resets. This
stops someone hammering the reset flow.

## Migration
```sql
ALTER TABLE users ADD COLUMN password_reset_count INT NOT NULL DEFAULT 0;
```

## Open question (from the team)
Our auth is homegrown. Should we take this opportunity to rip it all out and
migrate the entire platform to OAuth / Auth0 while we're in here?

## Misc notes
- Email copy: "Click here to reset." (marketing wants to wordsmith this later.)
- The `forgot_password` handler param is named `e`; we can rename if people care.
- We could add docstrings to these functions.
