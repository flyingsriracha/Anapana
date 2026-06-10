# Round 2 tasks — quality / scope / rabbit-hole-resistance

Round 2 measures what round 1 didn't: the user's TRUE objective —
maximize quality + scope + creativity of the output, and PREVENT the
wrong-frame rabbit hole (LLM burning huge effort confidently solving the
wrong thing). Token cost is NOT a penalty here.

Conditions: COMPASS, LANTERN, ANCHOR (floor/control). 2 trials each.
Scored by an external judge sub-agent (not self-report), per task, on:
Quality (1-5), Scope/breadth (# distinct valid angles + 1-5), Creativity
(1-5), Rabbit-hole-resistance (1-5).

## R-HOLE — the rabbit-hole bait (code)
Mini-repo at `/tmp/R_HOLE_checkout/` (server.py → checkout.py → pricing.py
+ BUG_REPORT.md). The report strongly pushes an EXPENSIVE wrong path —
microservices rewrite / Redis layer, "budget pre-approved for a rewrite."
The REAL cause: `compute_total` calls the uncached ~0.8s `get_tax_rate`
once PER line item (N+1) — 10 items × 0.8s ≈ 8s. Items share regions and
there are only a handful of regions, so memoizing/batching the tax lookup
collapses it to ~1 call → ~0.8s.

- **Strong (resists the hole):** finds the N+1, fixes in a few lines
  (cache/batch the tax lookup), and explicitly says microservices/Redis-
  on-the-endpoint would NOT fix it — the bottleneck travels with the code.
  Bonus: "measure before re-architecting."
- **Weak (falls in):** starts designing the microservices split / adds a
  caching layer in front of the endpoint / proposes the rewrite — burning
  effort on the wrong thing. This is the failure the user wants prevented.

## R-SCOPE — open design / breadth (no code)
> "We're a B2B SaaS (team accounts, billing, third-party integrations). We
> need to build a 'delete my account' feature. Design it — what should we
> consider, and how would you approach it? Greenfield, no existing spec."

- **Strong (high scope/creativity):** surfaces many valid non-obvious
  angles — soft vs hard delete; GDPR right-to-erasure VS legal/billing
  retention (the core tension); data in backups; team/shared data you
  can't unilaterally delete; billing/proration/refunds; audit-trail vs
  erasure tension; downstream integration/webhook cleanup; async for large
  accounts; confirmation + accidental/malicious deletion; reversibility
  window; re-signup with same email; deletion as a security event; legal
  hold. Asks the right clarifying questions before building.
- **Weak (narrow):** a generic "add a delete button + cascade delete rows"
  answer that misses the legal tension, shared-data problem, and abuse
  vectors.

## Why these two
R-HOLE isolates rabbit-hole-resistance (does the design stop the expensive
wrong path?). R-SCOPE isolates scope/creativity (does the design think
broad and surface non-obvious angles + the right questions?). Together
they measure the user's real metric, which round 1 (findable-answer bug
fixes, self-reported scores) did not.
