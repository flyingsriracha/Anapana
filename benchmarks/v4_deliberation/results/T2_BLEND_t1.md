# T2 MEMORY-DESIGN · arm=BLEND · trial=1 (raw solver output, verbatim)

## Step 1 — Reflex first
"Use a message queue (Kafka or SQS) for fan-out; standard pattern." I'd recommend a queue immediately because that's textbook for fan-out at 100k, without pausing to interrogate the constraint that forbids it.

## Step 2 — Triage
T1 cross-system (Postgres shared; multiple external providers; new system fitting an established policy) — yes. T2 framing pressure — prompt pre-loads a settled policy ("explicitly agreed NOT to introduce message queues"); suppressor framing that pre-empts the natural move; "Greenfield" subtly boxes it — yes. T3 expensive to roll back — greenfield architecture; yes. Score 3 → FULL.

## Step 3 — Step-back, then frame check
**0. Step-back:** class = high-fan-out, externally-rate-limited, durable delivery. Canonical solutions (tech-agnostic): durable work queues; scheduled polling of a pending-work table (approximates a queue in an RDBMS); chunked batch dispatch. Key property: bottleneck is the providers' rate limits + the need to retry transiently-failed deliveries without losing state. Durability + fan-out pacing are core.
**A.** Asked NOT to consider message queues — the single most natural fit. The constraint is in direct tension with the requirements; the prompt asks me to treat that tension as resolved.
**B.** Actual problem: deliver to 100k reliably, honor per-provider rate limits, retry failures, for synchronously-fired events. The constraint is a policy stated as settled — but was it established for cases with these properties?
**C.** Named authority + prior decision ("we explicitly agreed") — strongest framing pressure; asserts the decision is made and my job is implementation-within-constraints. Correct response: verify the prior decision was made with this use case in mind, not just comply.
**D. Counterfactual:** If "we explicitly agreed NOT to introduce message queues" were absent, would my answer change? Yes, dramatically — without it a queue (or queue-like durable buffer) is obviously right. The constraint flips my answer entirely → the constraint is the anchor; evaluate it, don't accept it.
**E. Memory/context as stale anchor:** prior decision = "sync REST over shared Postgres, no queues." Sync REST/Postgres is excellent for request/response services needing an immediate answer; the policy is almost certainly motivated by avoiding Kafka/Rabbit/SQS ops overhead. But notifications fan-out is structurally different: a REST endpoint receiving "send campaign" cannot synchronously call 100k provider endpoints (rate-limited/rejected; HTTP timeout; no retry within a sync call). The prior decision doesn't appear to have been made for this use case — applying it here is extending a rule beyond its intended scope.
**Result:** the stated task may be partially wrong; the constraint fits most of the platform but conflicts with this workload's requirements. Name the reframe clearly; surface the frame, then design.

## Step 4 — Trace at the right altitude
System: a sync REST service cannot fan out to 100k in one request without violating rate limits, timing out, losing retryability. Module: fan-out + rate-limit + retry is the central constraint, not internal service-to-service transport. The "no queues" policy addresses *external* service coupling via a broker; it does not address *internal* work-scheduling within one service. Distinction: (1) external broker as a dependency (likely prohibited) vs (2) internal work-queue pattern — a Postgres-backed outbox/job table, queue semantics on Postgres, not a separate broker. If read strictly as "no async work queues of any kind," the service can't be built correctly at scale; if read as "no external message broker," a Postgres job table satisfies both policy and requirements.

## Step 5 — Reproduce-gate + isolated re-derivation
No code; re-derive from first principles, framing set aside.
- Q1 fan-out honoring rate limits? Not synchronously; need (a) durable pending work, (b) a dispatcher consuming at allowed rate, (c) success-marking + retry scheduling = work-queue semantics regardless of implementation.
- Q2 implement on Postgres? Transactional outbox (`notification_jobs`, write in same txn as the event); `LISTEN/NOTIFY` for near-real-time; polling loop `WHERE status='pending' AND next_attempt_at<=now()` with `FOR UPDATE SKIP LOCKED`.
- Q3 failure modes? Without durable pending state, a crash mid-fan-out loses which of 100k were sent (unrecoverable); with a job table, restart resumes pending rows; idempotent delivery via `sent_at` prevents duplicates.
- Q4 require a broker? No — `FOR UPDATE SKIP LOCKED` suffices for a single-service work queue at 100k (Postgres within envelope at this scale).
Conclusion: Postgres-backed job table + polling workers is correct; honors "no external broker" while implementing fan-out + rate limits + retry.

## Step 6 — Compare and converge
| | Reflex | Framed (no-queues literal) | Isolated re-derivation |
|---|---|---|---|
| Mechanism | Postgres job table + polling | Unclear — sync REST doesn't fan out to 100k | Postgres job table + polling |
| Queue semantics | Yes (internal) | No (policy blocks) | Yes (internal, Postgres-native) |
| Viable at 100k? | Yes | No | Yes |
| Fits policy spirit? | Yes | Literal yes, practical no | Yes |
Reflex and isolated re-derivation agree; the literal no-queues framing is not viable. The gap is real and meaningful. Convergence reached; the disagreement with the framed answer is the finding — flag it, human decides.

## Step 7 — Inversion + alternatives (FULL)
Worse: synchronous HTTP fan-out from a long-running handler (timeouts, lost deliveries, no retry; silent: partial campaigns, no audit); Postgres without `SKIP LOCKED` (duplicate sends, thundering herd).
- **Alt 1 (accept constraint, Postgres job table — primary).** Down: Postgres bottleneck at very high sustained frequency; vacuum/bloat burden. Silent: workers die mid-campaign, rows stuck "processing" forever without a reaper → campaigns stall.
- **Alt 2 (revisit the constraint for this service).** Down: reopens a "settled" decision; political. Silent failure: none — technically correct path; risk is organizational.
- **Alt 3 (Postgres + pg_notify + separate workers).** Down: pg_notify payloads limited/ephemeral; if workers down when it fires, lost — must still poll. Silent: notification storms; workers can't back-pressure the notifier.
- **Alt 4 (do nothing/defer).** Business impact of no notifications isn't silent.

## Step 8 — Identity (delta)
Reflex: design within the constraint without questioning it. After: same technical design, but a clear flag that the constraint was made for a different context (request/response services) and may not have been intended to govern internal async delivery. The human must decide whether it applies here or whether this service's delivery engine is exempt. The reflex would have buried that.

# FINAL DESIGN RECOMMENDATION
**Policy question first:** "No queues" was made for sync backend services. A notifications service has two layers: (1) the service API — a REST endpoint accepting a campaign trigger, synchronous, returns 202 — fits the policy; (2) the delivery engine — internal async fan-out to 100k against rate-limited providers — categorically async; "synchronous REST" doesn't apply. Clarify whether the policy governs internal delivery engines or only service-to-service API surfaces. If only APIs (the more defensible reading), the delivery engine can use a proper queue internally without violating it.

**Design (constraint-compliant, Postgres-as-queue):**
```
Trigger API (REST, sync) → writes campaign + recipient rows (transactional) → 202
Dispatcher workers (N processes, SKIP LOCKED) → claim pending rows → enforce per-provider rate limits → call provider REST → write success/fail/retry
Reaper (periodic) → reclaim rows stuck 'processing' > T min → requeue
```
- Data model `campaigns` (id, created_at, status, channel) and `notifications` (id, campaign_id, user_id, channel, provider, status pending/processing/sent/failed/dead, attempts, next_attempt_at, claimed_at, provider_message_id, last_error). Partial index `(status, next_attempt_at)` where status IN ('pending','failed').
- Dispatcher: BEGIN → `SELECT ... WHERE status='pending' AND next_attempt_at<=now() ORDER BY next_attempt_at LIMIT :batch FOR UPDATE SKIP LOCKED` → set 'processing'+claimed_at → COMMIT → per row: check provider rate limit, call API (idempotency key = provider_message_id set on first attempt), on success 'sent', on transient error 'pending'+attempts+++backoff, on permanent 4xx 'dead', on max attempts 'dead'.
- Rate limiting: token bucket in worker memory (one worker/provider) OR `rate_limit_slots(provider, window_start, used)` with advisory lock; recommended: size worker pool per provider so `workers×batch×freq ≤ limit` (100k at 100/s ≈ 17 min; campaigns are batch, not real-time).
- Fan-out insertion: single `INSERT INTO notifications SELECT ... FROM users WHERE ...` server-side; batch 10k chunks if needed.
- Stuck-job reaper: `UPDATE ... SET status='pending', claimed_at=NULL WHERE status='processing' AND claimed_at < now() - interval '10 minutes'` every 5 min — without it, crashed workers strand rows.
- Retry: 1m/5m/15m/1h then dead; permanent errors (invalid number, unsubscribed) → dead immediately.
- Idempotency: provider_message_id = gen_random_uuid() on first attempt, reused as idempotency key (SendGrid/Twilio honor it).
- Observability: campaign-level GROUP BY status; worker heartbeats table (alert if silent >2 min during a campaign); dead-letter alert for review.
- Honest tradeoffs: throughput ceiling (SKIP LOCKED degrades under many concurrent workers; fine at 100k/campaign, few/day; revisit at millions/day); table bloat (archive sent rows after 30 days / partition by created_at); no native back-pressure (priority column for urgent vs bulk); operational complexity (you're re-implementing queue semantics a real queue gives free).

Summary: build the trigger API synchronous (202); implement the delivery engine as a Postgres job table with SKIP LOCKED workers, per-provider rate limiting via worker sizing, exponential backoff, idempotency keys, and a stuck-job reaper. Before finalizing, confirm whether "no queues" was meant to apply to internal delivery engines; if not, a lightweight queue (Oban/River) would be straightforwardly correct and reduce bespoke engineering. **Do not build until the policy question is resolved.**
