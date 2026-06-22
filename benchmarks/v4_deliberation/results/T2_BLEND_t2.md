# T2 MEMORY-DESIGN · arm=BLEND · trial=2 (raw solver output, verbatim)

## Step 1: Reflex first
Without this process: "The no-queue constraint makes fan-out hard. You'll need a background worker table in Postgres to queue jobs, a polling loop, and careful rate-limiting per provider. Use synchronous REST for each send." Frozen.

## Step 2: Triage
T1 cross-system (Postgres, email/SMS/push providers, new service) — yes. T2 framing pressure strong: "we explicitly agreed NOT to introduce message queues — settled policy" = authority pre-diagnosis + settled prior decision; "Greenfield" is a suppressor (clean-slate feel suppresses scrutiny). T3 expensive to roll back — yes. Score 3 → FULL.

## Step 3: Step-back, then frame check
**0. Step-back:** class = reliable high-throughput fan-out with heterogeneous external providers that have per-provider rate limits and require retry — i.e. "durable work queue with at-least-once delivery, fan-out, and back-pressure." This is one of the canonical use cases for message queues — because the required properties (durability, decoupling from the caller, retry, back-pressure, rate-limiting) map precisely onto what queues provide.
**A.** Asked NOT to consider message queues — and implicitly not to question whether "no queues" applies to this case. The framing assumes the policy was made with a fan-out service in mind; not stated.
**B.** Actual problem: reliable fan-out with rate-limiting + retry. The constraint is a prior policy from a different context (backend services on sync REST + Postgres). Does that context's policy fit this problem?
**C.** "we explicitly agreed..." = authority frame + settled-prior-decision suppressor (the primary anchor); "Greenfield" suppressor; the constraint is given before the problem (ordering matters — frame received before the design ask).
**D. Counterfactual:** If the constraint were "no external queue services (SQS/Kafka)" rather than "no message queues of any kind," the design is the same but framed differently. The single thing that would flip my answer: knowing what problem the "no queues" decision was actually solving (infra complexity? ops cost? lock-in? consistency?) — none given.
**E. Memory/context as stale anchor:** prior decision = "sync REST over shared Postgres, no queues" for *backend services* — a request/response API policy. Notifications fan-out is categorically different (fire-and-forget, 100k recipients, rate-limited providers, async retry). The policy is stale for this task — not wrong in general, but made for a different class of service and applied here by category analogy, not by considering this use case's tradeoffs.
**Result:** the stated task ("design without queues") may be the wrong task — it imports a policy from a different context. Surface it, then design under both framings.

## Step 4: Trace at the right altitude
System: properties needed = durability (no loss on crash), per-provider rate limits, retry-without-duplication, fan-out at scale (trigger can't block for 100k), observability. The constraint removes the canonical tool for the first four. Module: what does Postgres approximate a queue with? Persistent job table; `SELECT FOR UPDATE SKIP LOCKED` for concurrent claim without contention; `pg_notify` to wake workers; transactional durability — the "Postgres as queue" pattern (Que/Oban/Sidekiq-on-Postgres). Slower than a purpose-built queue, scaling limits (~few hundred jobs/s before Postgres I/O binds), but works at this load. At 100k/campaign this is a batch job (one event → 100k rows inserted → workers drain), not a real-time per-request queue.

## Step 5: Reproduce-gate + isolated re-derivation
No code; re-derive with framing set aside.
- Min for correctness: (a) durable pending list, (b) workers claim+execute, (c) retry tracking, (d) per-provider rate limiting, (e) idempotency to prevent duplicates on retry — delivery-queue semantics regardless of implementation.
- Postgres can implement all: outbox/job table, SKIP LOCKED, transactional acks, retry counter + next_attempt_at, per-provider rate-limit table/worker enforcement.
- What Postgres-as-queue does worse than a real queue: throughput ceiling (table bloat/vacuum under sustained high frequency — manageable at 100k/campaign); no native back-pressure / consumer groups (implement in worker code); dequeue latency under lock contention grows with worker count.
- What "no message queues" actually rules out: strictly, RabbitMQ/Kafka/SQS/NATS. Postgres-as-queue is debatable — queue semantics via an RDBMS; using Postgres for job queuing predates and is categorically different from "adding a message queue" in the ops/infra sense.
- Is the constraint wise here? For sync request/response sharing Postgres, sensible (limits infra surface, simple consistency). For async fan-out with provider rate limits, a poor fit technically but implementable; cost = engineering complexity a queue would otherwise absorb.
Result: Postgres approach viable but requires building queue semantics on Postgres explicitly; a real queue would be simpler/more scalable here. Constraint adds cost and caps throughput; doesn't make it impossible.

## Step 6: Compare and converge
| | Reflex | Framed (constraint) | Isolated re-derivation |
|---|---|---|---|
| Approach | Postgres job table + polling | Same | Same — viable |
| Constraint validity | Accepted unquestioned | Accepted | Questioned — from different context |
| Risk flagged | None | None | Yes — misfit for this class |
| Recommendation | Design within it | Design within it | Surface the misfit first, then design within it |
Gap: reflex+framed accept the constraint unquestioned; isolated re-derivation flags it was made for a different context. Targeted pass: the policy plausibly governs the service's external interface (sync REST trigger is natural), not its internal execution model (async by necessity). Even generously, introducing a queue (Postgres job table or dedicated) in the delivery layer is a meaningful choice the prior policy may have intended to prevent — can't resolve without the policy's intent. Convergence: both angles agree on the technical design (Postgres job table); they diverge on whether to accept the constraint — flag it, human decides. Stop.

## Step 7: FULL — Inversion + alternatives
Worse: fan-out synchronously in the HTTP handler (blocks for 100k, times out, campaign lost); one campaign-wide lock row (one failure blocks all); 10 workers polling without SKIP LOCKED (massive contention).
- **Alt 1 (Postgres job table — primary).** Down: Postgres bottleneck at very high sustained frequency; vacuum/bloat burden. Silent: workers die mid-campaign, rows stuck "processing" forever unless a stuck-job reaper runs → campaigns silently stall.
- **Alt 2 (revisit the constraint for this service).** Down: reopens "settled" decision; political. Silent: none — technically correct; risk organizational.
- **Alt 3 (Postgres + pg_notify, separate worker processes).** Down: pg_notify ephemeral/limited; lost if workers down → still need polling fallback. Silent: notification storms; no back-pressure.
- **Alt 4 (do nothing/defer).** Business impact not silent.

## Step 8: Identity (delta)
Reflex: design within the constraint without questioning it. After: same technical design, but a clear flag that the constraint is an anchor from a prior decision for request/response services, not async fan-out; the human must decide whether it applies here or whether the delivery engine is exempt. Technically the design is the same; the deliberation changed the *framing obligation* — I'm not just proposing an implementation, I'm flagging a constraint tension to adjudicate before building. The reflex skipped that step.

# FINAL DESIGN RECOMMENDATION
**Policy question first (human must answer before building):** a notifications service has two distinct layers: (1) the service API — REST endpoint accepting a campaign trigger, synchronous, returns 202 Accepted — fits the policy naturally; (2) the delivery engine — internal async fan-out to 100k against rate-limited providers — categorically async; "synchronous REST" semantics don't apply. Clarify whether the policy governs internal delivery engines or only service-to-service API surfaces. If only APIs (more defensible), the delivery engine can use a proper queue internally without violating it; if all infra including internal async, proceed with Postgres-as-queue below, eyes open to tradeoffs.

**Design (constraint-compliant, Postgres-as-queue):**
```
Trigger API (REST, sync) → writes campaign + recipient rows (transactional) → returns 202
Dispatcher workers (N processes, SKIP LOCKED) → claim pending rows → enforce per-provider rate limits → call provider REST → write success/fail/retry
Reaper (periodic, single process) → reclaim rows stuck processing > T min → requeue
```
- `campaigns` (id, created_at, status pending/in_progress/done, channel nullable).
- `notifications` (one row per recipient×channel): id, campaign_id, user_id, channel, provider, status pending/processing/sent/failed/dead, attempts, next_attempt_at, claimed_at, provider_message_id (dedup on retry), last_error. Partial index `(status, next_attempt_at)` where status IN ('pending','failed').
- Dispatcher (per channel/provider): BEGIN → `SELECT ... WHERE status='pending' AND next_attempt_at<=now() ORDER BY next_attempt_at LIMIT :batch FOR UPDATE SKIP LOCKED` → set 'processing'+claimed_at → COMMIT → per row: check per-provider rate limit, call API (idempotency key set on first attempt), success→'sent', transient→'pending'+attempts+++backoff, permanent 4xx→'dead', max attempts (5)→'dead'.
- Rate limiting per provider (SendGrid/Twilio/FCM/APNs): token bucket in worker memory (one worker/provider) OR `rate_limit_slots(provider, window_start, used)` atomic increment with advisory lock; recommended — size worker pool so `workers×batch×freq ≤ provider limit`; 100k batch over minutes (Twilio 100/s ≈ 17 min), not ms.
- Fan-out insertion: one server-side `INSERT INTO notifications SELECT ... FROM users WHERE ...`; batch 10k chunks if rows are very wide.
- Stuck-job reaper: `UPDATE ... SET status='pending', claimed_at=NULL WHERE status='processing' AND claimed_at < now() - interval '10 min'` every 5 min — without it crashed workers strand rows.
- Retry: attempt 1→1m, 2→5m, 3→15m, 4→1h, 5→dead; permanent provider errors (invalid number, unsubscribed) → dead immediately.
- Idempotency: provider_message_id = gen_random_uuid() on first attempt, passed as idempotency key on retries (SendGrid/Twilio dedup server-side).
- Observability: campaign-level GROUP BY status dashboard; worker heartbeats (alert if silent >2 min during a campaign); dead-letter alert for ops review.
- Does NOT handle well (honest tradeoffs): throughput ceiling (SKIP LOCKED degrades under many concurrent workers; fine at 100k/campaign few/day; revisit at millions/day — then revisit the constraint, don't patch); table bloat (archive sent after 30 days / partition by created_at); no native back-pressure (priority column to route urgent ahead of bulk); operational complexity (re-implementing SKIP LOCKED/reaper/idempotency/backoff a purpose-built queue gives free).

Summary: trigger API synchronous REST (202, policy-compliant); delivery engine = Postgres job table with SKIP LOCKED workers, per-provider rate limiting via worker sizing, exponential backoff, idempotency keys, stuck-job reaper. Before finalizing, confirm whether "no queues" was intended for internal delivery engines or only service APIs; if not, a lightweight queue (Postgres-backed Oban/River) would be straightforwardly correct and reduce bespoke engineering. **Do not build until the policy question is resolved** — the design is sound under the constraint, suboptimal if the constraint doesn't actually apply.
