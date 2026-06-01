# Bug report (filed by on-call engineer)

When our subscription-cancellation worker auto-refunds the unused portion
of a canceled subscription, `payments/charge.py:process_refund` is called
with `initiated_by=None` (it's a system-initiated refund — no human user
triggered it).

`AuditLog.log_event` crashes with `AttributeError: 'NoneType' object has no
attribute 'id'`. The refund itself succeeds at the payment provider, but
our function returns 500 to the worker, which then retries — causing
duplicate refunds in some cases.

**Please fix so that refunds work for both user-initiated and
system-initiated cases.**

You have access to the codebase at `./test_repo_2/`. Look at whatever you
need to.
