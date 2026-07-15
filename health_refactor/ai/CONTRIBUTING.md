# Contributing Guide — AI Service

> **Cursor rules** (monorepo): `../../.cursor/rules/` — collaboration workflow,
> API documentation, database migrations, and AI-specific conventions.

## Table of Contents
1. [Architecture overview](#architecture-overview)
2. [How to add a new runtime capability](#how-to-add-a-new-runtime-capability)
3. [How to add a new LLM provider](#how-to-add-a-new-llm-provider)
4. [How to add a new pipeline step](#how-to-add-a-new-pipeline-step)
5. [How to define request & response schemas](#how-to-define-request--response-schemas)
6. [How to add a new background worker task](#how-to-add-a-new-background-worker-task)
7. [How to write tests](#how-to-write-tests)
8. [Test and lint](#test-and-lint)
9. [Git workflow](#git-workflow)
10. [Auth — shared JWT secret](#auth--shared-jwt-secret)
11. [Calling the backend service](#calling-the-backend-service)
12. [Vector store migrations](#vector-store-migrations)
13. [API documentation for frontend](#api-documentation-for-frontend)

---

## Architecture overview

```
src/
├── presentation/api/      # FastAPI routers — HTTP/WS/SSE boundary only
│   └── v1/
│       ├── chat/          # POST /chat/message, GET /chat/stream
│       ├── voice/         # WS  /voice/stream
│       ├── evaluation/    # POST /evaluations/run
│       ├── indexing/      # POST /indexing/ingest
│       └── internal/      # Backend→AI callbacks (internal API key auth)
├── application/           # Pipelines / orchestrators (no HTTP, no LLM SDK)
│   ├── chat/
│   ├── voice/
│   ├── evaluation/
│   ├── indexing/
│   ├── retrieval/
│   ├── tool_executor/
│   └── summarisation/
├── domain/                # Pure types, interfaces, prompt contracts
│   ├── agent/
│   ├── conversation/
│   ├── evaluation/
│   ├── knowledge_base/
│   └── tool/
└── infrastructure/        # LLM clients, vector store, storage, workers
    ├── llm/
    ├── vector_store/
    ├── storage/
    ├── backend_client/
    └── workers/
```

Dependency rule: presentation → application → domain ← infrastructure.
The domain layer contains ZERO LLM SDK imports and ZERO HTTP calls.

---

## How to add a new runtime capability

1. Define the domain interface in `src/domain/<capability>/interfaces.py`
   using a `Protocol`.
2. Implement the pipeline in `src/application/<capability>/pipeline.py`
   with a class that has a single `async def run(self, ctx: ...)` method.
3. Wire dependencies in `src/application/<capability>/dependencies.py`.
4. Expose a FastAPI route in `src/presentation/api/v1/<capability>/router.py`.
5. Add unit tests under `tests/unit/application/<capability>/`
   and e2e tests under `tests/e2e/<capability>/`.

---

## How to add a new LLM provider

1. Implement `ILLMClient` (defined in `src/domain/llm/interfaces.py`)
   in a new file under `src/infrastructure/llm/providers/<provider>.py`.
2. Register the provider in `src/infrastructure/llm/factory.py`
   keyed by the provider slug (e.g. `"anthropic"`).
3. Add `<PROVIDER>_API_KEY` to `.env.example`.
4. Write unit tests in `tests/unit/infrastructure/llm/`.

LLM calls NEVER happen inside the domain layer.
All LLM logic lives in infrastructure; the application layer calls
the interface only.

---

## How to add a new pipeline step

Each pipeline is a sequence of `Step` objects defined in
`src/application/<module>/steps/`. A step receives a typed context
object, performs one transformation, and returns the mutated context.

```python
# src/application/chat/steps/retrieve_context.py
class RetrieveContextStep:
    def __init__(self, retriever: IRetriever) -> None:
        self._retriever = retriever

    async def run(self, ctx: ChatContext) -> ChatContext:
        ctx.retrieved_chunks = await self._retriever.search(
            query=ctx.last_user_message,
            agent_id=ctx.agent_id,
            top_k=5,
        )
        return ctx
```

Add the step to the pipeline's `STEPS` list in
`src/application/<module>/pipeline.py`.

---

## How to define request & response schemas

All HTTP schemas live in `src/presentation/api/v1/<module>/schemas.py`.

Internal schemas (between pipeline steps) live in
`src/application/<module>/schemas.py`.

Never leak infrastructure types (raw LLM response objects) into
the application or presentation layers — always map to domain types.

---

## How to add a new background worker task

1. Create a task file in `src/infrastructure/workers/tasks/<module>.py`.
2. Decorate with `@dramatiq.actor` (set `max_retries` for API-heavy jobs).
3. Call application-layer pipelines from the task — never LLM SDKs directly.
4. Import the task module in `src/infrastructure/workers/broker.py` so the actor registers.
5. Run workers in a second terminal: `make worker`.

---

## How to write tests

### Unit tests (`tests/unit/`)
- Mirror `src/` exactly.
- All LLM calls mocked with `respx` or `unittest.mock.AsyncMock`.
- Test pipeline steps in isolation by injecting mock dependencies.

### Integration tests (`tests/integration/`)
- Test vector store operations against a real pgvector instance.
- Test document chunking and indexing against actual PDF/DOCX fixtures.

### E2E tests (`tests/e2e/`)
- Use FastAPI `AsyncClient`.
- Mock LLM provider responses with `respx` fixtures.
- Assert full streaming output for chat/voice routes.

---

## Test and lint

Run these from the **AI repo root** (`product-dashboard-ai/`).

### Setup (once)

```bash
cp .env.example .env
pip install -r requirements.txt
# optional: conda activate venv/
```

### Commands

| Command | What it does |
|---------|----------------|
| `make lint` | `ruff check src/ tests/` |
| `make format` | `ruff format src/ tests/` |
| `make test` | Unit + integration tests with **90% coverage** gate |
| `make test-integration` | Integration tests only (`-m integration`) |
| `make dev` | Local API on port **8001** (`uvicorn --reload`) |
| `make worker` | Dramatiq worker for indexing / summarisation tasks |

Examples:

```bash
make lint
make test
```

`make test` runs `pytest tests/unit tests/integration --cov-fail-under=90`.
Some integration and worker paths are skipped or omitted from coverage until
Redis, pgvector, and Dramatiq are available locally.

### CI

GitHub Actions (`.github/workflows/ci.yml`) runs `make lint` then `make test` on
push/PR to `dev` and `main`. Deploy to Render dev is manual via
**Actions → Deploy to Dev** (`.github/workflows/deploy-dev.yml`).

---

## Git workflow

Branching, PRs, and releases (`dev` → `main`) are documented in
**[docs/git-workflow.md](docs/git-workflow.md)**.

Summary:

- Branch from **`dev`**: `feature/...` or `fix/...`
- Open PRs into **`dev`** (not `main`) for normal work
- Release: PR **`dev` → `main`** when ready for production
- Deploy Render dev manually via **Actions → Deploy to Dev**

---

## Auth — shared JWT secret

The AI service **never mints tokens**. It only verifies them.

```python
# src/core/security.py
def verify_token(token: str) -> TokenPayload:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
```

Both services must have the same `JWT_SECRET_KEY` value in their `.env`.
On rotation: deploy backend first (new secret), then AI service.
See ADR-002 in `docs/architecture/adr/`.

The **internal API key** (`INTERNAL_API_KEY`) is a separate pre-shared
secret used for backend→AI server-to-server calls that do not carry a
user JWT (e.g. triggering an indexing job after a KB upload).

---

## Calling the backend service

Use `src/infrastructure/backend_client/client.py`. It attaches the
shared JWT or internal API key automatically and handles retries.

```python
backend = BackendClient()
await backend.patch_ticket(ticket_id=ticket_id, payload={"status": "resolved"})
await backend.post_ticket_summary(ticket_id=ticket_id, payload=summary)
```

Never call `httpx` directly from application or domain code.

---

## Vector store migrations

The AI service uses a **separate** Postgres database for embeddings (pgvector),
configured via `VECTOR_STORE_URL` in `.env`. This is **not** the product
backend `dashboard` database.

Migrations are **not** run on app startup. Schema changes are applied only via
Alembic (same pattern as the backend and admin services).

### Commands

When Alembic is configured under `src/infrastructure/vector_store/migrations/`:

```bash
# Generate a new migration (after changing vector store ORM models)
make migrate-gen name="add_document_chunks_index"

# Apply all pending migrations
make migrate

# Roll back the most recent migration
make migrate-down

# (Optional) Inspect migration state
alembic -c src/infrastructure/vector_store/migrations/alembic.ini current
alembic -c src/infrastructure/vector_store/migrations/alembic.ini history
```

If `make migrate` is not defined yet, use the `alembic -c ...` commands directly
until the Makefile targets are added.

### Where things live

| Item | Path |
|------|------|
| ORM models | `src/infrastructure/vector_store/models.py` (and sibling modules as added) |
| Vector store access | `src/infrastructure/vector_store/pgvector.py` |
| Migration revisions | `src/infrastructure/vector_store/migrations/versions/` |
| DB URL | `VECTOR_STORE_URL` in `.env` |

### How to add a new vector store table (or column)

1. **Model** — Add or update SQLAlchemy models under
   `src/infrastructure/vector_store/` (extend the shared `Base` for that store).
2. **Register** — Ensure all models are imported where Alembic builds
   `target_metadata` (typically a `models` package `__init__.py`).
3. **Generate** — `make migrate-gen name="add_<description>"`
4. **Review** — Check the generated revision (pgvector extension, indexes,
   `USING` casts for type changes).
5. **Apply** — `make migrate`

For pgvector, the first migration often enables the extension:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Rules

- Do **not** call `create_all()` on app startup for the vector store.
- Keep **domain** and **application** layers free of SQLAlchemy / pgvector imports.
- Prefer **`String`** for categorical fields unless you need Postgres enums.
- For **asyncpg** URLs, use `?ssl=require`, not `sslmode=require`.

### Fresh database

If `VECTOR_STORE_URL` points at an empty database, `make migrate` creates
tables from all pending revisions and records the version in `alembic_version`.

---

## API documentation for frontend

Docs live under `docs/api/`, mirroring `src/presentation/api/v1/<module>/`.

```
docs/api/
├── README.md
├── endpoints.md
└── v1/
    ├── chat/         ← include SSE streaming notes
    ├── voice/        ← include WebSocket message format
    ├── evaluation/
    ├── indexing/
    └── internal/     ← INTERNAL_API_KEY, not user JWT
```

### When to document

- **After** the route is implemented — not for stubs.
- Document SSE/WebSocket behavior in **Frontend notes**.
- Update `docs/api/endpoints.md` summary table.

See `../../.cursor/rules/api-documentation.mdc` for the full template.

See also `../../.cursor/rules/database-migrations.mdc`.
