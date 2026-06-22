# T2 MEMORY-DESIGN · arm=SATORI · trial=1 (raw solver output, verbatim)

## Step 1 — Reflex First
Without this process: "use a message queue (Kafka or SQS) to fan out to workers per channel, with rate-limit buckets and a retry queue — the textbook answer." I would have recommended a queue immediately and not paused to interrogate the constraint that forbids it.

## Step 2 — Triage
T1 cross-system (Postgres shared; multiple providers; new system fitting an established policy) — yes. T2 framing pressure — the prompt pre-loads a settled policy ("explicitly agreed NOT to introduce message queues — settled"); suppressor-style framing that pre-empts the natural design move — yes. T3 expensive to roll back — greenfield architecture sets the standard; yes. Score 3 → FULL.

## Step 3 — Frame Check
**A.** Asked NOT to consider durable message queues — the most proven pattern for exactly this problem — removed before I reason.
**B.** Actual problem: reliable delivery at 100k fan-out with per-provider rate limits + retries. Hidden question: does "no queues" actually apply here, or does this requirement expose the limits of a policy formulated for standard request/response services? Notifications are inherently asynchronous, durable, fan-out, rate-controlled over minutes/hours — categorically different.
**C.** Social/framing pressure to comply and produce a design. Honest move: surface whether compliance produces a sound system. Stated task may be the wrong task — at minimum contains a material tension I must surface before designing. Will produce two designs: one honest about no-queue tradeoffs, one I'd actually build.

## Step 4 — Trace (zoom)
System: notifications fan-out = asynchrony + per-provider rate limiting + durability + independent partial-failure retry. Module: the critical choice is how work is queued/tracked. In a Postgres-only architecture there are three mechanisms: (1) a jobs/tasks table polled by workers (Postgres-as-queue / transactional outbox); (2) synchronous inline delivery with cron retry; (3) scheduled batch sweeps. **All three ARE queues functionally** — durable stores of pending work. "Postgres job table" vs "message queue" is implementation, not concept; the Postgres-as-queue pattern IS a queue with worse operational characteristics for this workload. Behavior: at 100k, synchronous inline (even 100ms/call) ≈ 2.8 hours, blocking; retry-per-row needs careful locking. Right altitude: the issue is whether "no queues" is coherent with the requirements — a policy-level finding to surface, then design at module level assuming the policy holds.

## Step 5 — Reproduce Gate (predicted failure modes)
- Synchronous inline delivery on event → the HTTP request blocks for hours; can't fix without making delivery async (reintroducing a queue).
- Postgres jobs table with pollers → works, but row-lock contention at scale; `SELECT ... FOR UPDATE SKIP LOCKED` is itself a queue primitive; at 100k rows + retry + rate-limit the jobs table becomes the bottleneck.
- Cron-batch → delivery latency bounded below by the cron interval; coarse retries.
- Rate limits without a queue → workers must track limits; without shared state they over-fire and get throttled; with Postgres shared state they contend on locks.
These are predictions (greenfield, nothing to run), grounded in known Postgres-under-concurrency and job-queue-pattern behavior.

## Step 6 — FULL: Inversion + Alternatives
Worse: synchronous fan-out of 100k in one request, retrying in the HTTP loop — timeouts, duplicate sends, no partial-completion visibility, no crash recovery.
**A. Postgres transactional outbox / jobs table (compliant).** On event, write one row per recipient in the same txn; workers poll `FOR UPDATE SKIP LOCKED`, deliver, update status; per-provider token-bucket rows. Up: no new infra; durable; observable; fits policy. Down: Postgres not built for high-throughput queues — polling latency, VACUUM pressure, index bloat; rate-limit coordination adds latency. Silent failure: dead rows accumulate faster than VACUUM, bloat degrades the shared instance for unrelated services.
**B. Lightweight queue (honest recommendation).** Redis Streams / SQS for fan-out; Postgres = system of record. Up: ack/visibility-timeout/dead-letter are exactly what's needed; rate limiting at consumer; workers scale w/o Postgres lock contention. Down: new dependency; ops knowledge; team decided against. Silent failure: queue down → notifications stop (need dead-letter + monitoring).
**C. Managed notification platform (Knock/Courier/SendGrid).** Thin API layer; platform handles fan-out/rate-limit/retry/routing; Postgres records status via webhooks. Up: eliminates the infra problem; fast; "no queue in your infra." Down: cost at scale; vendor dependency; less control. Silent failure: opaque vendor outages.

## Step 7 — Identity (delta)
Reflex: "use a queue (Kafka/SQS); standard pattern." Process changed: (1) caught that the constraint applied to THIS workload is incoherent with the requirements — 100k fan-out + rate limits + retries is definitionally a queue problem regardless of implementation; (2) forced me to name Postgres-as-queue as a queue-in-disguise rather than a clean constraint-compliant alternative; (3) surfaced the VACUUM-pressure silent failure; (4) added Alt C (managed platform) — question whether to build at all. Reflex would have produced a confident design; the process produced a policy challenge + three alternatives with failure modes + an honest recommendation.

# FINAL DESIGN RECOMMENDATION
**Policy tension (state before deciding):** "No queues" was formulated for synchronous backend services; this task is categorically async. Every viable implementation — including Postgres job tables — is a queue functionally. Revisit the policy with this use case in scope. If the intent was "no new infra dependencies," the Postgres-jobs approach honors it; if literally "no async fan-out patterns," the requirements can't be met safely. Surface this before committing.

**If the constraint holds — Postgres transactional outbox:**
- Schema: `notification_campaigns` (creator, template, status, timestamps); `notification_jobs` (recipient_id, channel, status pending/in_flight/delivered/failed/dead, attempt_count, next_attempt_at, provider_message_id, last_error); `provider_rate_limits` (provider, tokens_available, last_refill_at, optimistic decrement under FOR UPDATE).
- Fan-out trigger: launching a campaign inserts all 100k rows in batches (~1000/txn); API returns immediately; status tracked on the campaign row.
- Workers: pool of processes; `SELECT id ... WHERE status='pending' AND next_attempt_at<=NOW() LIMIT 50 FOR UPDATE SKIP LOCKED`; check provider token bucket; call provider; on transient failure increment attempt + exponential backoff (1m,5m,30m,2h,8h), after N → dead; commit.
- Rate limiting: per-provider token row refilled on a schedule; workers decrement before sending; hot-row at high worker counts → short lock windows, tune batch sizes.
- Ops: aggressive autovacuum on notification_jobs (`autovacuum_vacuum_scale_factor=0.01`), archive delivered/dead rows; cap workers per provider; dashboard (pending/in_flight/dead, per-provider rate); idempotency keys (e.g. SendGrid x-message-id) to prevent duplicate sends on retry.
- Ceiling: sub-minute latency for huge campaigns and sustained >~5k/min will strain Postgres — plan for it.

**Honest recommendation:** Greenfield → ship Alternative C (managed platform) first; you get fan-out, rate limiting, retries, routing, receipts without building/operating any of it. The Postgres jobs design is buildable but consumes significant engineering on non-core problems. Scope "no queues" to synchronous business-logic services, not async delivery infra. If the team won't change the policy and won't use a managed platform: build the Postgres outbox with explicit VACUUM tuning and a documented capacity ceiling before the first campaign — don't discover the VACUUM problem in production.
