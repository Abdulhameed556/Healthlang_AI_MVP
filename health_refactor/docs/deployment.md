# Deployment

The platform ships as **one Docker image** (built from the repo-root `Dockerfile`)
that runs as **two process types** off the same codebase:

| Process | Command | Purpose |
|---------|---------|---------|
| **web** | `gunicorn run:root_app -c gunicorn.conf.py` | Serves the HTTP API (admin + backend + AI in one app — see `run.py`), including the Freshchat webhook. Listens on `:8000`. |
| **worker** | `dramatiq ai.src.infrastructure.workers.worker --processes 1 --threads 8` | Dramatiq background worker: processes queued jobs — Freshchat inbound bot replies, KB indexing, post-close ticketing, etc. |

Both require **PostgreSQL** and **Redis**. The web `Dockerfile` `CMD` already runs
gunicorn; the **worker runs the same image with the command overridden**.

> Why a separate worker? Inbound Freshchat messages (and other long jobs) are
> enqueued by the web process and executed by the worker. **Without the worker
> running, webhooks are accepted but the bot never replies.**

## Prerequisites

- PostgreSQL 16 (one database; apps use separate tables)
- Redis 7 (sessions, dedup, handoff state, Dramatiq broker)
- A populated `.env` copied from [`.env.example`](../.env.example) (see **Environment variables** below)

## 1. Build the image

```bash
docker build -t supportos-platform:latest .
```

The image (`Dockerfile`):

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "run:root_app", "-c", "gunicorn.conf.py"]
```

## 2. Run database migrations (once per deploy)

Run before starting web/worker so the schema is current:

```bash
docker run --rm --env-file .env supportos-platform:latest \
  sh -c "PYTHONPATH=. alembic -c backend/src/infrastructure/database/migrations/alembic.ini upgrade head"
```

(Admin tables are included in the same backend migration chain; see
`admin/src/infrastructure/database/migrations/README.md`.)

## 3. Run the web process

```bash
docker run -d --name supportos-web \
  --env-file .env -p 8000:8000 \
  supportos-platform:latest
# uses the image CMD: gunicorn run:root_app -c gunicorn.conf.py
```

Tunables (env, read by `gunicorn.conf.py`):

| Env | Meaning | Default |
|-----|---------|---------|
| `PORT` / `APP_PORT` | Bind port | `8000` |
| `WEB_CONCURRENCY` / `GUNICORN_WORKERS` | Gunicorn workers | `max(2, CPU count)` |
| `GUNICORN_TIMEOUT` | Worker timeout (s) | `120` |
| `LOG_LEVEL` | Log level | `info` |

## 4. Run the worker process

Same image, **override the command**:

```bash
docker run -d --name supportos-worker \
  --env-file .env \
  supportos-platform:latest \
  sh -c "PYTHONPATH=. dramatiq ai.src.infrastructure.workers.worker --processes 1 --threads 8"
```

- `--processes` × `--threads` = concurrent jobs per container. Scale by raising
  these or running more worker containers.
- The worker needs **no inbound port** (it pulls from Redis).
- It must share the **same `REDIS_URL` and `DATABASE_URL`** as the web process.
- The worker entrypoint sets `DATABASE_USE_NULL_POOL=true` automatically; you do
  not need to set it in `.env` unless running a custom worker command.

Locally this is `make worker` (see `Makefile`).

## docker-compose

The committed [`docker-compose.yml`](../docker-compose.yml) runs `db`, `redis`,
and `app` (web) for local dev. To also run the worker, add a service that reuses
the same build and overrides the command:

```yaml
  worker:
    build: .
    depends_on: [db, redis]
    env_file: .env
    command: sh -c "PYTHONPATH=. dramatiq ai.src.infrastructure.workers.worker --processes 1 --threads 8"
```

## Platform (Render / Heroku-style) mapping

Define two services from the same repo/image:

| Service type | Start command |
|--------------|---------------|
| Web service | `gunicorn run:root_app -c gunicorn.conf.py` (binds `$PORT`) |
| Background worker | `PYTHONPATH=. dramatiq ai.src.infrastructure.workers.worker --processes 1 --threads 8` |

Add managed Postgres + Redis and point `DATABASE_URL` / `REDIS_URL` at them. Run
the migration command as a pre-deploy/release step.

## Environment variables

**Source of truth:** [`.env.example`](../.env.example) — copy to `.env` and set
values for your environment. Every key in that file maps to `os.getenv(...)` in
`backend/src/core/config.py`, `admin/src/core/config.py`, or `ai/src/core/config.py`.

### Required for production

| Var | Notes |
|-----|-------|
| `DATABASE_URL` | `postgresql+asyncpg://…` (shared by web + worker) |
| `REDIS_URL` | `redis://…` (shared by web + worker) |
| `JWT_SECRET_KEY` | Backend product JWT — must differ from `ADMIN_JWT_SECRET_KEY` |
| `ADMIN_JWT_SECRET_KEY` | Admin panel JWT |
| `API_TOOL_SECRETS_ENCRYPTION_KEY` | Fernet key; API tool + integration secrets at rest |
| `CORS_ORIGINS` | Comma-separated allowed browser origins (**required when `APP_ENV` is not `development`**) |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GROQ_API_KEY` | At least one LLM key for the worker |

### CORS (local dev vs production)

| `APP_ENV` | `CORS_ORIGINS` | Behaviour |
|-----------|----------------|-----------|
| `development` | unset or blank | **All origins allowed** — no CORS config needed locally |
| `development` | set | Only listed origins |
| `production` (etc.) | unset | Falls back to localhost defaults — **set explicitly in deploy** |
| `production` (etc.) | set | Only listed origins |

### App / runtime

| Var | Default | Notes |
|-----|---------|-------|
| `APP_NAME` | `SupportOS Backen` | Display name |
| `APP_SLUG` | `supportos-backend` | Slug for generated email addresses |
| `APP_ENV` | `development` | `development` \| `production` |
| `APP_DEBUG` | `false` | Enables `/docs` when `true` |
| `APP_PORT` | `8000` | HTTP bind port |
| `LOG_LEVEL` | `INFO` | |
| `DATABASE_SQL_ECHO` | `false` | SQLAlchemy echo |
| `DATABASE_POOL_*` | see `.env.example` | Connection pool tuning |
| `DATABASE_USE_NULL_POOL` | `false` | Worker sets this automatically |

### Backend — auth, email, storage

See `.env.example` sections **BACKEND** and **JWT** for:
`JWT_*`, `PRODUCT_APP_BASE_URL`, `INVITATION_EXPIRE_HOURS`, `PASSWORD_RESET_EXPIRE_HOURS`,
`EMAIL_*`, `MAILGUN_*`, `SMTP_*`, `STORAGE_BACKEND`, `AWS_*`, `GOOGLE_*`,
`SEND_INVITATION_EMAIL_IN_DEV`, `SEND_PASSWORD_RESET_EMAIL_IN_DEV`.

### Internal service keys

| Var | Notes |
|-----|-------|
| `AI_SERVICE_BASE_URL` | Backend → AI HTTP base |
| `AI_SERVICE_INTERNAL_API_KEY` | Backend → AI auth |
| `BACKEND_BASE_URL` | AI → backend HTTP base |
| `BACKEND_INTERNAL_API_KEY` | AI → backend auth |
| `INTERNAL_API_KEY` | AI service internal routes |
| `ADMIN_INTERNAL_API_KEY` | Admin → backend internal routes |

### AI / worker — LLM & vector store

| Var | Default | Notes |
|-----|---------|-------|
| `OPENAI_API_KEY` | | |
| `ANTHROPIC_API_KEY` | | |
| `GROQ_API_KEY` | | |
| `GOOGLE_API_KEY` / `GEMINI_API_KEY` | | |
| `DEFAULT_LLM_PROVIDER` | `openai` | |
| `DEFAULT_CHAT_MODEL` | `gpt-4o` | |
| `DEFAULT_EMBEDDING_MODEL` | `text-embedding-3-small` | |
| `VECTOR_STORE_BACKEND` | `pinecone` | |
| `VECTOR_STORE_URL` | `DATABASE_URL` | |
| `PINECONE_API_KEY` | | |
| `PINECONE_INDEX_NAME` | `supportos` | |
| `DRAMATIQ_BROKER_URL` | `REDIS_URL` | |

### Freshchat

See [Freshchat integration](backend_docs/architecture/freshchat-integration.md).

| Var | Required | Default | Notes |
|-----|----------|---------|-------|
| `API_PUBLIC_BASE_URL` | yes (for webhooks) | `""` | Public base URL of this backend; no trailing slash |
| `FRESHCHAT_WEBHOOK_PUBLIC_KEY` | no | `""` | Fallback RSA PEM (`\n` allowed on one line) |
| `FRESHCHAT_HANDOFF_STATUS` | no | `new` | Group queue status for IntelliAssign |
| `FRESHCHAT_HANDOFF_RELEASE_ACTIONS` | no | `conversation_resolution,conversation_reopen` | Un-mute bot on these webhook actions |
| `FRESHCHAT_RESOLVE_STATUS` | no | `resolved` | Status when bot ends chat |
| `FRESHCHAT_WEBHOOK_CAPTURE_TO_FILE` | no | off | Debug: write raw payloads to disk |

### Admin panel

| Var | Notes |
|-----|-------|
| `ADMIN_JWT_*` | Admin session JWT |
| `ADMIN_EMAIL_FROM` | From address for admin emails |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | `make seed` only |
| `MAX_FAILED_LOGIN_ATTEMPTS` | Lockout threshold |

## Health & verification

- Web health: `GET <base>/api/v1/health` → `200`.
- Worker health: it logs `worker_task_start` / `worker_task_end` lines; a Freshchat
  turn also emits a green `freshchat_timing …` summary.
- After deploy, send a test message on a routed Freshchat channel and confirm a
  `queued: true` webhook log (web) followed by a `worker_task_end` (worker).

## Scaling notes

- **Web** scales by `WEB_CONCURRENCY` and/or more web containers (stateless).
- **Worker** scales by `--processes`/`--threads` and/or more worker containers.
  Each Dramatiq job runs on its own event loop and persists synchronously, so
  multiple workers are safe; Freshchat messages are deduplicated by message id.
- Postgres uses `NullPool` in worker job loops; size DB connections for the total
  worker concurrency across containers.

## Related

- [`.env.example`](../.env.example) — full environment variable template
- [Freshchat integration architecture](backend_docs/architecture/freshchat-integration.md)
- [Workers overview](ai_docs/workers/README.md)
- [setup.md](setup.md) — local dev setup
