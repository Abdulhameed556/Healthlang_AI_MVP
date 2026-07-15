# Contributing Guide

> **Cursor rules** (monorepo): `../../.cursor/rules/` — collaboration workflow,
> API documentation, database migrations, and backend-specific conventions.

## Table of Contents
1. [Architecture overview](#architecture-overview)
2. [Application module layout (commands, results, services)](#application-module-layout-commands-results-services)
3. [Standard API response envelope](#standard-api-response-envelope)
4. [How to add a new API endpoint](#how-to-add-a-new-api-endpoint)
5. [How to add a new use-case](#how-to-add-a-new-use-case)
6. [HTTP request & response schemas](#http-request--response-schemas)
7. [Email (templates + providers)](#email-templates--providers)
8. [How to add a new repository](#how-to-add-a-new-repository)
9. [How to write tests](#how-to-write-tests)
10. [Test and lint](#test-and-lint)
11. [Git workflow](#git-workflow)
12. [Database migrations](#database-migrations)
13. [API documentation for frontend](#api-documentation-for-frontend)

---

## Architecture overview

```
src/
├── presentation/api/      # FastAPI routers — HTTP boundary only
│   └── v1/
│       ├── auth/
│       ├── agents/
│       ├── tickets/
│       └── ...
├── application/           # Use-cases / orchestration (no HTTP, no DB)
│   ├── auth/
│   ├── agents/
│   └── ...
├── domain/                # Pure business logic, entities, interfaces
│   ├── auth/
│   ├── agents/
│   └── ...
└── infrastructure/        # DB, storage, email, external HTTP clients
    ├── database/
    ├── repositories/
    ├── storage/
    └── ...
```

Dependency rule: presentation → application → domain ← infrastructure.
The domain layer NEVER imports from any other layer.

---

## Application module layout (commands, results, services)

Each bounded context under `src/application/<module>/` uses the same folder
layout. Reference implementation: **`users`** (admin provision invited super-admin).

```
src/application/users/
├── commands/              # use-case input (dataclasses)
│   ├── __init__.py
│   └── admin.py           # CreateInvitedUserFromAdminCommand
├── results/               # use-case output (dataclasses)
│   └── admin.py           # CreateInvitedUserFromAdminResult
├── ports/                 # outbound interfaces (typing.Protocol)
│   └── email.py           # IInvitationEmailSender
├── services/              # stateless helpers (no HTTP, no DB)
│   └── invitation_tokens.py
├── use_cases/             # one file per story
│   └── create_invited_user_from_admin.py
└── dependencies/
    ├── __init__.py        # re-export get_* for routers
    ├── providers.py       # FastAPI: wire repos → use-case class
    └── infrastructure.py  # cached infra singletons (e.g. email sender)
```

### Naming (do not mix layers)

| Layer | Type name | Example | Lives in |
|-------|-----------|---------|----------|
| HTTP request body | `*Request` | `CreateInvitedUserFromAdminRequest` | `presentation/.../schemas.py` |
| HTTP payload in `data` | `*Response` | `CreateInvitedUserFromAdminResponse` | `presentation/.../schemas.py` |
| Use-case input | `*Command` | `CreateInvitedUserFromAdminCommand` | `application/.../commands/` |
| Use-case output | `*Result` | `CreateInvitedUserFromAdminResult` | `application/.../results/` |
| Outbound contract | `I*` (Protocol) | `IInvitationEmailSender` | `application/.../ports/` |
| Pure helper | functions / small class | `generate_invitation_token()` | `application/.../services/` |

**Rule:** Map in the router only — `Request` → `Command` → `execute()` → `Result` → `Response` → wrap in `ApiResponse`.

| Folder | Contains | Does not contain |
|--------|----------|------------------|
| `commands/` / `results/` | Dataclasses for `execute()` | Pydantic, FastAPI |
| `ports/` | Protocols for email, payments, etc. | SQLAlchemy |
| `services/` | Token/link builders, shared steps | `Depends()`, HTTP |
| `use_cases/` | `execute(command) -> result` | JSON parsing |
| `dependencies/providers.py` | `get_<use_case>()` factories | Business rules |

### End-to-end example (admin → invited user)

```
Admin Portal
    POST /api/v1/internal/admin/users  (+ X-Admin-Api-Key)
        │
        ▼
presentation/endpoints/create_invited_user.py
    CreateInvitedUserFromAdminRequest  →  CreateInvitedUserFromAdminCommand
    Depends(get_create_invited_user_from_admin)
        │
        ▼
application/users/use_cases/create_invited_user_from_admin.py
    repos + IInvitationEmailSender
    services/invitation_tokens (token + link)
        │
        ▼
infrastructure/repositories/ + infrastructure/email/
    templates/invitation.html  +  provider (log | smtp | mailgun)
        │
        ▼
ApiResponse[CreateInvitedUserFromAdminResponse]  →  JSON to client
```

---

## Standard API response envelope

**Every** JSON endpoint returns the same top-level shape:

```json
{
  "message": "Human-readable summary",
  "status_code": 200,
  "error": false,
  "data": { }
}
```

| Field | Success | Error |
|-------|---------|-------|
| `message` | e.g. `"Invited user created successfully"` | e.g. `"Not found"` |
| `status_code` | Matches HTTP status (200, 201, …) | Matches HTTP status (401, 404, …) |
| `error` | `false` | `true` |
| `data` | Business payload | Usually `null`; validation may use `{"errors": [...]}` |

Helpers: `src/presentation/schemas/api_response.py` (`ApiResponse`, `success()`, `error_body()`).
Domain errors, `HTTPException`, and request validation are wrapped in
`src/presentation/error_handlers.py`.

```python
from src.presentation.schemas.api_response import ApiResponse, success

@router.post("/users", response_model=ApiResponse[CreateInvitedUserFromAdminResponse], status_code=201)
async def create_invited_user(...) -> ApiResponse[CreateInvitedUserFromAdminResponse]:
    result = await use_case.execute(command)
    return success(
        CreateInvitedUserFromAdminResponse.model_validate(result),
        message="Invited user created successfully",
        status_code=201,
    )
```

---

## Rich Swagger / OpenAPI (automatic docs)

When `APP_DEBUG=true`, open **`/docs`** (Swagger UI) or **`/redoc`**.

| Piece | Location |
|-------|----------|
| Global API intro + envelope docs | `src/presentation/openapi/config.py` |
| Tag categories (agents, auth, …) | `src/presentation/openapi/tags.py` |
| Status codes + examples | `envelope_responses()` in `src/presentation/openapi/responses.py` |

**Adding a new endpoint** — no hand-written OpenAPI YAML:

1. Put **`Field(..., description=...)`** and `json_schema_extra.example` on Pydantic schemas.
2. Set router **`tags=["module-name"]`** (must exist in `openapi/tags.py`).
3. On the route, add **`summary`**, **`description`**, and:

```python
from src.presentation.openapi import ERROR_ADMIN_INTERNAL, envelope_responses

@router.post(
    "/users",
    summary="Short title for Swagger",
    description="Longer markdown-friendly explanation.",
    response_model=ApiResponse[MyResponse],
    status_code=201,
    responses=envelope_responses(
        MyResponse,
        success_status=201,
        success_message="Created",
        errors=ERROR_ADMIN_INTERNAL,  # or ERROR_JWT, ERROR_CRUD, custom tuple
    ),
)
```

**Error presets:** `ERROR_UNAUTHORIZED`, `ERROR_JWT`, `ERROR_ADMIN_INTERNAL`, `ERROR_CRUD` — pick the closest set.

---

## How to add a new API endpoint

1. Create (or open) the router under `src/presentation/api/v1/<module>/`.
2. Add Pydantic schemas in `schemas.py` (`*Request`, `*Response` for `data`).
3. Handler must:
   - Validate body/query with `*Request`
   - Map to `*Command` and call **one** use-case `execute()`
   - Map `*Result` to `*Response` and return `success(...)` inside `ApiResponse[T]`
4. Register the router in `src/presentation/api/v1/router.py`.
5. Tests mirror `src/` exactly — see [How to write tests](#how-to-write-tests).
6. After implementation, add `docs/api/v1/<module>/<endpoint>.md` and a row in `docs/api/endpoints.md`.

Example:
```python
# src/presentation/api/v1/internal/admin/endpoints/create_invited_user.py
@router.post("/users", response_model=ApiResponse[CreateInvitedUserFromAdminResponse], status_code=201)
async def create_invited_user_from_admin(
    body: CreateInvitedUserFromAdminRequest,
    use_case: CreateInvitedUserFromAdmin = Depends(get_create_invited_user_from_admin),
) -> ApiResponse[CreateInvitedUserFromAdminResponse]:
    result = await use_case.execute(
        CreateInvitedUserFromAdminCommand(
            email=str(body.email),
            organization_name=body.organization_name,
            # ...
        )
    )
    return success(
        CreateInvitedUserFromAdminResponse.model_validate(result),
        message="Invited user created successfully",
        status_code=201,
    )
```

---

## How to add a new use-case

1. Add `*Command` in `src/application/<module>/commands/<topic>.py`.
2. Add `*Result` in `src/application/<module>/results/<topic>.py`.
3. Add `src/application/<module>/use_cases/<name>.py` with `async def execute(command) -> result`.
4. Inject repositories and **ports** via `__init__` (not FastAPI).
5. Register `get_<use_case>()` in `dependencies/providers.py`; export from `dependencies/__init__.py`.
6. Unit test: `tests/unit/application/<module>/use_cases/test_<name>.py`.

```python
# application/users/use_cases/create_invited_user_from_admin.py
class CreateInvitedUserFromAdmin:
    def __init__(
        self,
        organization_repository: IOrganizationRepository,
        user_repository: IUserRepository,
        invitation_repository: IInvitationRepository,
        invitation_email_sender: IInvitationEmailSender,
    ) -> None:
        ...

    async def execute(
        self, command: CreateInvitedUserFromAdminCommand
    ) -> CreateInvitedUserFromAdminResult:
        ...
```

---

## HTTP request & response schemas

Presentation schemas live in `src/presentation/api/v1/<module>/schemas.py`.

- **Request** — Pydantic `BaseModel` (JSON body / query).
- **Response** — Pydantic model for the object placed inside envelope **`data`**.
- Use `model_config = ConfigDict(from_attributes=True)` when building from dataclasses/ORM.
- Never expose internal fields (e.g. `password_hash`).

Application **Command** / **Result** stay as dataclasses in `application/` — not Pydantic.

```python
# presentation — HTTP
class CreateInvitedUserFromAdminRequest(BaseModel):
    email: EmailStr
    organization_name: str
    ...

class CreateInvitedUserFromAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    organization_id: UUID
    user_id: UUID
    invitation_token: str
    ...

# application — use-case
@dataclass(frozen=True)
class CreateInvitedUserFromAdminCommand:
    email: str
    organization_name: str
    ...
```

---

## Email (templates + providers)

Outbound email is infrastructure-only; use-cases depend on **ports**.

```
src/infrastructure/email/
├── types.py                 # EmailMessage
├── registry.py              # register_provider, get_email_provider()
├── invitation_sender.py     # implements IInvitationEmailSender
├── template_email_sender.py # send(to, subject, template_name, context)
├── templates/
│   ├── renderer.py          # render_template / render_text_template by name
│   ├── invitation.html      # one HTML file per template (+ optional .txt)
│   └── invitation.txt
└── providers/
    ├── log.py               # EMAIL_PROVIDER=log (default dev)
    ├── smtp.py              # EMAIL_PROVIDER=smtp
    └── mail_gun.py          # EMAIL_PROVIDER=mailgun
```

Env: `EMAIL_PROVIDER`, `EMAIL_FROM`, `MAILGUN_*`, `SMTP_*` — see `.env.example`.

Tests mirror paths: `tests/unit/infrastructure/email/providers/test_mail_gun.py`, etc.

---

## How to add a new repository

1. Define the **abstract interface** in `src/domain/<module>/repositories.py`:
   ```python
   class IAgentRepository(Protocol):
       async def get_by_id(self, id: UUID) -> Agent | None: ...
       async def save(self, agent: Agent) -> Agent: ...
   ```
2. Implement it in `src/infrastructure/repositories/<module>.py`
   using SQLAlchemy models.
3. Bind the interface → implementation in
   `src/infrastructure/database/dependencies.py`.

---

## How to write tests

### Unit tests (`tests/unit/`)
- **Mirror `src/` folder structure exactly** — same directories and `test_<module>.py` names.
- Use `pytest` + `pytest-asyncio`.
- Mock all I/O with `unittest.mock.AsyncMock`.
- One test file per source module (use-case, provider, loader, endpoint).

Examples:

| Source | Test |
|--------|------|
| `application/users/use_cases/create_invited_user_from_admin.py` | `tests/unit/application/users/use_cases/test_create_invited_user_from_admin.py` |
| `application/agents/services.py` | `tests/unit/application/agents/services/test_services.py` |
| `infrastructure/repositories/agents.py` | `tests/unit/infrastructure/repositories/test_agents.py` |
| `infrastructure/email/providers/mail_gun.py` | `tests/unit/infrastructure/email/providers/test_mail_gun.py` |
| `presentation/.../endpoints/create_invited_user.py` | `tests/unit/presentation/.../endpoints/test_create_invited_user.py` |
| `presentation/api/v1/agents/endpoints/deploy.py` | `tests/unit/presentation/api/v1/agents/endpoints/test_deploy.py` |

Do **not** add extra directory levels under `tests/` that are not in `src/` (e.g. avoid `tests/unit/infrastructure/repositories/agents/`).

Leading underscores on source files (`_agent_mappers.py`) → drop the underscore in the test name (`test_agent_mappers.py`).

The `tests/unit/infrastructure/email/` package needs `tests/__init__.py` chain so pytest does not confuse it with the stdlib `email` module.

### Endpoint tests (FastAPI)

- Override `Depends` on `app` (`src/main.py`); always `app.dependency_overrides.clear()` in `finally`.
- Match the handler dependency: `require_auth` for list/get; `require_org_inviter` for admin-only mutations.
- **403 read-only:** override `require_auth` with `UserRole.READ_ONLY` only — leave `require_org_inviter` unmocked so the real role check runs.

### Repository unit tests

- Mock `AsyncSession` with `AsyncMock` for async methods (`flush`, `execute`, …).
- Use `MagicMock` for sync methods like `session.add` (`assert_called_once()`, not `assert_awaited_once()`).

### Integration tests (`tests/integration/`)
- Use a real test DB (spin up with `docker compose`).
- Test repository implementations against actual Postgres.
- Use `pytest` fixtures in `tests/conftest.py` that create/tear down
  isolated DB transactions.

### E2E tests (`tests/e2e/`)
- Use FastAPI's `TestClient` / `AsyncClient`.
- Test complete request → response flows for every endpoint.
- Seed the DB with `factory-boy` factories from `tests/factories/`.

---

## Test and lint

Run these from the **backend repo root** (`product-dashboard-backend/`).

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
| `make dev` | Local API on port **8000** (`uvicorn --reload`) |

Examples:

```bash
make lint
make test
```

`make test` runs `pytest tests/unit tests/integration --cov-fail-under=90`.
Integration repository tests are skipped until a real test DB and `db_session`
fixture are configured.

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

## Database migrations

Migrations are **not** run on app startup. Schema changes are applied only via Alembic.

### Commands

```bash
# Generate a new migration (after changing ORM models)
make migrate-gen name="add_ticket_summary_table"

# Apply all pending migrations
make migrate

# Roll back the most recent migration
make migrate-down

# (Optional) Inspect migration state
alembic -c src/infrastructure/database/migrations/alembic.ini current
alembic -c src/infrastructure/database/migrations/alembic.ini history
```

### Where things live

| Item | Path |
|------|------|
| ORM models | `src/infrastructure/database/models/` |
| Model registry (for autogenerate) | `src/infrastructure/database/models/__init__.py` |
| Migration revisions | `src/infrastructure/database/migrations/versions/` |
| Alembic config | `src/infrastructure/database/migrations/alembic.ini` |
| DB URL | `DATABASE_URL` in `.env` |

### How to add a new table (or column)

1. **Model** — Create or edit a file under `src/infrastructure/database/models/`
   (extend `Base` from `src/infrastructure/database/base.py`).
2. **Register** — Import the model in `src/infrastructure/database/models/__init__.py`
   so Alembic autogenerate sees it.
3. **Generate** — `make migrate-gen name="add_<description>"`
4. **Review** — Open the new file under `migrations/versions/` and verify
   `upgrade()` / `downgrade()` (especially enum → string casts if you change types).
5. **Apply** — `make migrate`

### Rules

- Do **not** call `Base.metadata.create_all()` in the application.
- Prefer **`String`** columns for categorical/status fields unless you need
  Postgres enum enforcement at the DB level.
- For **asyncpg** URLs (e.g. Aiven), use `?ssl=require` in `DATABASE_URL`, not
  `sslmode=require` (asyncpg does not accept `sslmode`).

### Fresh database

If the database is empty, `make migrate` creates all tables from pending
revisions and records the version in `alembic_version`.

---

## API documentation for frontend

Docs live under `docs/api/`, mirroring `src/presentation/api/v1/<module>/`.

```
docs/api/
├── README.md
├── endpoints.md
└── v1/
    ├── auth/
    ├── users/
    ├── organizations/
    ├── agents/
    └── ... (see docs/api/README.md)
```

### When to document

- **After** the endpoint is implemented — not for stubs.
- One file per route: `docs/api/v1/<module>/<endpoint>.md`
- Include: **URL** (`<base>/api/v1/...` + environment table), summary, auth, sample request body, **envelope** success/error JSON (`data` field), frontend notes.
- Update `docs/api/endpoints.md` summary table (include local full URL example column).
- Example: `docs/api/v1/internal/admin/create-invited-user.md`
- Base URL convention: `docs/api/README.md` § Base URL

See `../../.cursor/rules/api-documentation.mdc` for the full template.

See also `../../.cursor/rules/database-migrations.mdc`.
