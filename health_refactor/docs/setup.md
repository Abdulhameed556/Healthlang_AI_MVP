# Local development setup

Guide to installing dependencies, configuring environment variables, running migrations,
and starting the app with the internal demo UI.

**Monorepo layout:** product backend + AI chat + admin panel share one Postgres database
and one `.env` at the repo root.

---

## Prerequisites

Install these on your machine (we do **not** use Docker Compose for local dev):

| Requirement | Version / notes |
|-------------|-----------------|
| **Python** | 3.11+ |
| **PostgreSQL** | Running locally; create a database (default name `supportos`) |
| **Redis** | Running locally on `localhost:6379` (sessions/cache; app starts without it for basic flows but some features expect it) |
| **make** | Used for dev commands (macOS/Linux) |

Optional for **test chat** (LLM orchestration):

| Provider | Env var | Notes |
|----------|---------|--------|
| Groq | `GROQ_API_KEY` | Default orchestration provider in code |
| OpenAI | `OPENAI_API_KEY` | Fallback model in orchestration config |

See `ai/src/infrastructure/chat_system/v1/orchestration/config.py` for default models.

---

## 1. Clone and enter the repo

```bash
cd product-dashboard-backend
```

---

## 2. Python virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 3. Environment file

```bash
cp .env.example .env
```

Edit `.env` for your machine. Minimum for local dev:

### App

```env
APP_ENV=development
APP_DEBUG=true
```

`APP_ENV=development` is required for the demo UI at `/demo/`.

### Database

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/supportos
```

Create the database if it does not exist:

```bash
createdb supportos
# or via psql: CREATE DATABASE supportos;
```

### Redis

```env
REDIS_URL=redis://localhost:6379/0
```

### Auth (backend JWT)

Generate a secret and set:

```env
JWT_SECRET_KEY=<64-char hex or strong random string>
```

### API tool encryption (required for API tools CRUD)

Generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set in `.env`:

```env
API_TOOL_SECRETS_ENCRYPTION_KEY=<fernet key>
```

### LLM keys (for demo chat)

Add at least one provider used by orchestration:

```env
GROQ_API_KEY=...
OPENAI_API_KEY=...
```

Optional overrides:

```env
DEFAULT_LLM_PROVIDER=openai
DEFAULT_CHAT_MODEL=gpt-4o
```

### Admin JWT (if using admin panel)

```env
ADMIN_JWT_SECRET_KEY=<different from JWT_SECRET_KEY>
```

See `.env.example` for the full list (email, S3, Google OAuth, internal API keys, etc.).

---

## 4. Database migrations

From the repo root (with venv active):

```bash
make migrate          # single migration chain (backend + admin tables, shared DB)
```

`make admin-migrate` is an alias for `make migrate`. All revisions live under
`backend/src/infrastructure/database/migrations/` and are recorded in
`alembic_version_backend`. See `admin/src/infrastructure/database/migrations/README.md`.

---

## 5. Seed admin account (optional)

For the **admin panel** only:

```bash
make seed
```

Uses `SEED_ADMIN_EMAIL` and `SEED_ADMIN_PASSWORD` from `.env`.

Product **demo UI** login uses a normal organization user (invited via admin or
existing test account) — there is no public self-signup.

---

## 6. Run the development server

Single process: product API + AI routes + demo UI on port **8000**.

```bash
make dev-backend
```

| URL | Purpose |
|-----|---------|
| http://localhost:8000/demo/ | Agent studio demo UI |
| http://localhost:8000/docs | OpenAPI (when `APP_DEBUG=true`) |
| http://localhost:8000/api/v1/ | Product + AI REST API |

Open the demo in a browser:

```bash
make dev-demo
```

---

## 7. Demo workflow

1. Start server: `make dev-backend`
2. Open http://localhost:8000/demo/
3. **Sign in** with a product dashboard user (email/password)
4. **Create agent** — brand, rules, scenarios, API tools
5. **Deploy agent** — required before chat
6. **Test chat** — create session, send messages

Details: [demo-ui/README.md](../demo-ui/README.md)

Chat API docs: [ai_docs/api/v1/chat/README.md](ai_docs/api/v1/chat/README.md)

Architecture: [ai_docs/architecture/chat-pipeline.md](ai_docs/architecture/chat-pipeline.md)

---

## Other make targets

```bash
make help            # List commands
make dev             # Alternate entry (run.py root app)
make dev-admin       # Admin API only → :8002
make dev-ai          # AI-only on :8001 (optional; not needed for demo)
make lint            # ruff check
make format          # ruff format
make test            # Full test suite (90% coverage gate)
make test-backend    # Backend tests only
make test-ai         # AI unit tests only
```

---

## Troubleshooting

### `Missing .env`

```bash
cp .env.example .env
```

### Database connection errors

- Confirm Postgres is running.
- Check `DATABASE_URL` user, password, host, and database name.
- Run `make migrate`.

### Demo UI 404

- Set `APP_ENV=development`.
- Use `make dev-backend` (not a UI-only static server).
- Ensure `demo-ui/` exists at repo root.

### Chat returns errors / 502 on tools test

- External API URLs must be reachable from your machine.
- Check API tool auth headers and query parameter names.

### Chat agent does not reply / LLM errors

- Set `GROQ_API_KEY` and/or `OPENAI_API_KEY`.
- Check server logs for provider errors.

### Agent chat: 409 on create session

- **Publish then deploy** the agent first (`POST /api/v1/agents/{id}/publish`, then `POST /api/v1/agents/{id}/versions/{version_id}/deploy`, or Publish + Deploy in demo UI).

---

## Documentation index

| Topic | Path |
|-------|------|
| Contributing | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| Backend API | [backend_docs/api/README.md](backend_docs/api/README.md) |
| AI architecture | [ai_docs/architecture/overview.md](ai_docs/architecture/overview.md) |
| Chat pipeline | [ai_docs/architecture/chat-pipeline.md](ai_docs/architecture/chat-pipeline.md) |
| Git workflow | [backend_docs/git-workflow.md](backend_docs/git-workflow.md) |
