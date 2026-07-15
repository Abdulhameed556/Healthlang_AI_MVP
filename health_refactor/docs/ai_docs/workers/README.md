# Background jobs (Dramatiq)

How the AI service runs work **after** the HTTP request returns — e.g. auto-closing
inactive chat sessions, generating ticket summaries, indexing documents.

We use **Dramatiq** with a **Redis** broker. The pattern below keeps Dramatiq
contained to one package and gives every job a typed, documented contract.

**See also:** [../architecture/session-close-and-ticketing.md](../architecture/session-close-and-ticketing.md)
· [../architecture/chat-pipeline.md](../architecture/chat-pipeline.md)

---

## How it flows

```
API / pipeline  ──enqueue_*()──►  Redis (broker)  ──►  Worker process  ──►  task ──► use-case
ai/src/infrastructure/workers/enqueue.py            make worker            tasks/   application/
```

- **Producers** (API, pipeline) call a helper in `enqueue.py`. They never import an
  actor or call `.send()` directly.
- **Redis** holds queued (and delayed) messages.
- **Worker** (`make worker`) imports `broker.py`, which registers all actors, then
  processes messages.

---

## Folder layout

```
ai/src/infrastructure/workers/
  broker.py                # Configures the global broker + imports every task module
  enqueue.py               # Public API: typed helpers to queue jobs (the only .send() site)
  _base.py                 # Shared helpers: run_async(), logging
  tasks/
    health_check.py        # Smoke-test task (reference template)
    post_close.py          # Summarise a closed session + create its ticket
    session_close_check.py # Delayed grace-timeout check for pending_close sessions
```

Business logic lives in `ai/src/application/...` and is called **by** tasks. Task
modules stay thin and must not contain pipeline logic.

---

## Run locally

1. Redis running (default broker URL: `redis://localhost:6379/2`, override with
   `DRAMATIQ_BROKER_URL`). `docker compose up -d` from `ai/` starts Redis.
2. **Terminal 1 — API:** `make dev-backend`
3. **Terminal 2 — worker:** `make worker`

`make worker` runs:

```bash
PYTHONPATH=. dramatiq ai.src.infrastructure.workers.worker --processes 1 --threads 8
```

> Always point Dramatiq at `ai.src.infrastructure.workers.worker` (not `...broker`).
> The `worker` entrypoint sets `DATABASE_USE_NULL_POOL=true` before the database
> engine is built, so each task opens a fresh connection on its own event loop.
> Running `...broker` directly (or without that env var) reuses pooled connections
> across short-lived task loops and fails with "Event loop is closed". If your
> deployment can't use this module, set `DATABASE_USE_NULL_POOL=true` in the
> worker process's environment instead.

---

## Smoke test

With the API and worker running:

```bash
curl -X POST http://localhost:8000/api/v1/internal/workers/test \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'
```

API responds `202 Accepted`:

```json
{ "enqueued": true, "task": "test_task", "message": "hello", "enqueued_at_iso": "..." }
```

The **worker terminal** logs:

```
worker_task_start task=test_task payload={'message': 'hello', ...}
worker_task_end   task=test_task result={'outcome': 'processed', ...}
```

If the API returns `503`, Redis is unreachable. If the API returns `202` but no
worker log appears, the worker process is not running.

---

## Task contract

Every task declares **Input**, **Output**, and a **purpose docstring**. See
`tasks/health_check.py` as the reference:

```python
@dataclass(frozen=True)
class TestTaskInput:
    message: str
    enqueued_at_iso: str

@dataclass(frozen=True)
class TestTaskResult:
    outcome: str
    echoed_message: str
    enqueued_at_iso: str
    processed_at_iso: str

@dramatiq.actor(max_retries=3, queue_name="default")
def test_task(message: str, enqueued_at_iso: str) -> dict:
    ...
```

Module docstring must state: **Purpose / Triggered by / Input / Output / Idempotent**.

---

## Add a new task (checklist)

1. **Use-case** — implement business logic in `ai/src/application/<domain>/...`
   (async, testable, no Dramatiq import).
2. **Contracts** — define `XInput` / `XOutput` frozen dataclasses (JSON-safe fields only).
3. **Task** — add `tasks/<name>.py` with `@dramatiq.actor`; the actor parses args,
   calls the use-case (use `run_async()` for async), returns `asdict(output)`.
4. **Register** — import the module in `broker.py`.
5. **Enqueue helper** — add `enqueue_<name>(...)` in `enqueue.py` (the only `.send()` site).
6. **Call site** — call the helper from the pipeline/API **after** the DB transaction commits.
7. **Test** — unit-test the use-case; assert `enqueue_<name>` calls `.send()` (mock the actor).
8. **Register in docs** — add a row to the table below.

---

## Conventions

| Rule | Why |
|------|-----|
| Producers call `enqueue.py` only | Dramatiq stays contained; jobs are discoverable |
| JSON-safe args (UUID/str/int/dict) | Messages serialize cleanly; never pass ORM objects |
| Enqueue **after** commit | Worker reads committed state, not an open transaction |
| Idempotent tasks | Re-read state at start; safe on retries / duplicate delivery |
| Delayed jobs via `send_with_options(delay=ms)` | Grace-period timers (e.g. session auto-close) |
| No LLM work in timer tasks | Keep timers cheap; do LLM work in a separate task |
| Structured logging | Always log task name + key ids + outcome |

---

## Task registry

| Task | Input | Output | Purpose | Status |
|------|-------|--------|---------|--------|
| `test_task` | `message`, `enqueued_at_iso` | `outcome`, `echoed_message`, timestamps | Smoke-test the worker pipeline | done |
| `process_post_close` | `session_id`, `enqueued_at_iso` | `outcome`, `created_ticket`, `reason`, `ticket_id?`, `worth_ticket?` | Summarise a closed session + create its ticket | done |
| `schedule_session_close_check` | `session_id`, `enqueued_at_iso` | `outcome`, `check_outcome`, `reason` | Auto-close a `pending_close` session after the grace window (delayed); chains `process_post_close` on close | done |

**Triggers** (enqueued from `ai/src/application/chat/pipeline.py` and the close-check task):

- `process_post_close` — after a turn closes the session (`end_conversation` /
  `transfer_to_live_support`), and after a grace-timeout `auto_timeout` close.
- `schedule_session_close_check` — delayed (`delay = grace_seconds * 1000`) when a
  turn enters `pending_close`.

See [../architecture/session-close-and-ticketing.md](../architecture/session-close-and-ticketing.md)
for the full flow.

---

## Code

| Piece | Path |
|-------|------|
| Broker + registration | `ai/src/infrastructure/workers/broker.py` |
| Enqueue API | `ai/src/infrastructure/workers/enqueue.py` |
| Shared helpers | `ai/src/infrastructure/workers/_base.py` |
| Reference task | `ai/src/infrastructure/workers/tasks/health_check.py` |
| Trigger endpoint | `ai/src/presentation/api/v1/internal/endpoints/workers.py` |
| Run command | `Makefile` → `make worker` |
