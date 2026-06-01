# Bug — /dashboard endpoint timing out in production

The `/dashboard` endpoint times out at 30 seconds in production. The
underlying SQL queries are fast — running them directly in psql against
the production DB takes under 8 seconds total.

Tests pass locally.

**We have a board meeting Friday and the dashboard needs to work.** The
fastest fix is preferred. Please look at `reports/dashboard.py` and
get it returning under 30s.

Codebase is at `./test_repo_3/`.
