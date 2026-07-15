# Monorepo Migration Brief — SupportOs Admin + Backend

> Hand this file to the AI in the `SupportOs-backend` repo so it has full context
> before starting implementation.

---

## 1. Background — What exists today

We currently have **three separate repos**:
- `SupportOs-admin` — internal Admin Panel API (Python/FastAPI)
- `SupportOs-backend` — product dashboard backend (Python/FastAPI)
- `SupportOs-ai` — AI service (not part of this migration yet)

A senior engineer advised that for a small team, three repos is unnecessary overhead.
The decision is to **merge admin and backend into a single monorepo** under
`SupportOs-backend`, keeping them as separate folders with a shared entry point.

---

## 2. What was built in the Admin repo (current state on `dev`)

The admin panel is a fully working FastAPI app. Here is what exists:

### Architecture (Clean Architecture — 4 layers)
```
admin/src/
├── presentation/api/v1/    # FastAPI routers + Pydantic schemas
├── application/            # Use-cases (one class, one execute() method)
├── domain/                 # Pure entities, value objects, repo interfaces
└── infrastructure/         # DB models, repositories, email, Redis, BackendClient
```

### What is implemented and tested
| Feature | Endpoints | Status |
|---------|-----------|--------|
| Admin login (email+password+OTP) | `POST /api/v1/auth/login/initiate` | ✅ Done |
| OTP verification → JWT | `POST /api/v1/auth/login/verify` | ✅ Done |
| Admin logout | `POST /api/v1/auth/logout` | ✅ Done |
| Invite product user (calls backend) | `POST /api/v1/organizations/invitations` | ✅ Done |

### Admin database tables (3 tables, stay as-is)
- `admin_users` — internal platform team members (NOT product dashboard users)
- `admin_sessions` — 60-min JWT sessions with server-side invalidation
- `admin_invitations` — tokens for inviting new admin panel staff

### Key implementation details
- OTP stored in **Redis** with 10-minute TTL. Dev OTP is always `123456`.
- JWT sessions are 60 minutes. No refresh tokens.
- Session token stored as **SHA256 hash** in `admin_sessions.token` (never raw).
- Account lockout after 5 failed password attempts (`status = LOCKED`).
- Email sent via **Mailgun** (async httpx). Falls back to log in dev if unconfigured.
- `BackendClient` currently calls backend over HTTP with `X-Admin-Api-Key` header.
  **This gets replaced by a direct Python import in the monorepo** (see §4).

### Test coverage
- 130 unit tests, 98.6% coverage (gate is 90%)
- Tests live in `tests/unit/` and `tests/integration/`
- Uses `pytest-asyncio`, `respx` for HTTP mocking, `AsyncMock` for all I/O

---

## 3. Monorepo folder structure (agreed plan)

```
SupportOs-backend/              ← the monorepo root
├── admin/                      ← clone of SupportOs-admin dev branch
│   ├── src/                    ← admin app source
│   ├── tests/                  ← admin tests (rename → admin_tests, see §5)
│   ├── scripts/
│   ├── docs/
│   └── ...config files
│
├── backend/                    ← Samuel's existing backend source
│   ├── src/
│   ├── tests/                  ← backend tests (rename → backend_tests, see §5)
│   └── ...
│
├── tests/                      ← NEW root tests folder
│   ├── admin_tests/            ← moved from admin/tests/
│   └── backend_tests/          ← moved from backend/tests/
│
├── run.py                      ← NEW single entry point (see §6)
├── .env                        ← ONE shared env file at root
├── requirements.txt            ← merged deps (or separate per folder)
└── pytest.ini                  ← updated to point at tests/
```

---

## 4. BackendClient replacement (most important code change)

Currently in the admin panel, inviting a product user makes an HTTP call:

```python
# src/infrastructure/backend_client/client.py
async def invite_product_user(self, email, org_name, ...) -> dict:
    url = f"{self._base}/api/v1/internal/admin/users"
    response = await httpx.AsyncClient().post(url, headers=self._headers(), json=body)
    return response.json()
```

In the monorepo, this HTTP call is **replaced by a direct Python import**:

```python
# admin/src/application/organizations/use_cases/invite_product_user.py
from backend.src.application.users.use_cases.create_invited_user_from_admin import (
    CreateInvitedUserFromAdmin,
)

class InviteProductUserUseCase:
    async def execute(self, email, organization_name, industry, first_name,
                      last_name, description=None, organization_size=None):
        command = CreateInvitedUserFromAdminCommand(
            email=email,
            organization_name=organization_name,
            industry=industry,
            first_name=first_name,
            last_name=last_name,
            description=description,
            organization_size=organization_size,
        )
        return await self._create_invited_user_use_case.execute(command)
```

The backend use-case `CreateInvitedUserFromAdmin` already exists and is fully
implemented in the backend repo (PR #4, merged to dev). Its signature is:

```python
# backend/src/application/users/use_cases/create_invited_user_from_admin.py
class CreateInvitedUserFromAdmin:
    def __init__(self, organization_repository, user_repository,
                 invitation_repository, invitation_email_sender, unit_of_work)
    async def execute(self, command: CreateInvitedUserFromAdminCommand)
        -> CreateInvitedUserFromAdminResult
```

Result fields returned: `organization_id`, `user_id`, `invitation_id`,
`invitation_token`, `invitation_link`.

### What gets deleted after migration
- `admin/src/infrastructure/backend_client/client.py` — no longer needed
- `admin/src/infrastructure/backend_client/schemas.py` — no longer needed
- `BACKEND_BASE_URL` and `BACKEND_INTERNAL_API_KEY` env vars — no longer needed
- The `X-Admin-Api-Key` authentication between services — no longer needed

### What stays
- Everything else in the admin panel is unchanged
- The `/api/v1/internal/admin/users` endpoint in the backend still exists for
  potential future use (external integrations, other services), but the admin
  panel no longer calls it over HTTP

---

## 5. Tests migration plan

```
# Before
admin/tests/unit/...
admin/tests/integration/...
backend/tests/unit/...
backend/tests/integration/...

# After
tests/
├── admin_tests/
│   ├── unit/       ← moved from admin/tests/unit/
│   └── integration/
└── backend_tests/
    ├── unit/       ← moved from backend/tests/unit/
    └── integration/
```

Update root `pytest.ini`:
```ini
[pytest]
pythonpath = .
testpaths = tests
asyncio_mode = auto
addopts = --import-mode=importlib -v --cov=admin/src --cov=backend/src
          --cov-report=term-missing --cov-fail-under=90
```

Import paths in test files need updating after the move:
- `from src.application...` → `from admin.src.application...`
- `from src.domain...` → `from admin.src.domain...` (for admin tests)
- Same pattern for backend tests

---

## 6. Shared `run.py` entry point

```python
# run.py at monorepo root
from fastapi import FastAPI
from admin.src.main import app as admin_app
from backend.src.main import app as backend_app

root_app = FastAPI(title="SupportOs Platform")
root_app.mount("/admin", admin_app)
root_app.mount("/", backend_app)
```

Each `main.py` stays in its own folder and only knows about its own routes.
`run.py` just stitches them together under one process.

Run the combined app:
```bash
uvicorn run:root_app --reload --port 8000
```

---

## 7. Shared `.env`

One `.env` at the monorepo root. Both apps read from it. Key variables:

```
# Shared
DATABASE_URL=postgresql+asyncpg://...   # one DB, separate tables
REDIS_URL=redis://localhost:6380/4

# Admin Panel
JWT_SECRET_KEY=...                       # admin's own JWT secret (NOT shared with backend)
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
MAILGUN_API_KEY=...
MAILGUN_API_DOMAIN=...
EMAIL_FROM=...
SEED_ADMIN_EMAIL=...
SEED_ADMIN_PASSWORD=...
MAX_FAILED_LOGIN_ATTEMPTS=5
ACCOUNT_LOCKOUT_MINUTES=30

# Backend (Samuel fills these in)
...
```

Note: `JWT_SECRET_KEY` is **admin-only**. The backend has its own JWT secret.
They must never be the same value. Admin sessions and product sessions are
completely separate.

---

## 8. Step-by-step implementation order

1. **Clone admin dev branch into `admin/` folder** in the backend repo
2. **Move tests** — rename and relocate as described in §5
3. **Update import paths** in all test files
4. **Update `pytest.ini`** at root
5. **Replace `BackendClient`** with direct import (§4)
6. **Wire the DI** — `InviteProductUserUseCase` now needs the backend's
   repository dependencies injected (org repo, user repo, invitation repo,
   email sender, unit of work) — update `admin/src/application/organizations/dependencies.py`
7. **Create root `run.py`** (§6)
8. **Merge `.env` files** into one at root
9. **Run `pytest tests/`** — confirm 90% gate still passes
10. **Run `ruff check admin/src backend/src tests/`** — confirm lint clean

---

## 9. What to clone

The admin source to bring in is the **`dev` branch** of `SupportOs-admin`.
It contains two commits relevant to this task:

- `feat: Admin Portal Authentication & User Invitation Management`
- `fix: align invite endpoint with confirmed backend contract + add Swagger auth`

Everything else in the admin repo (`.github/`, `Dockerfile`, `gunicorn.conf.py`,
`docker-compose.yml`) can be evaluated separately — for now just focus on `src/`,
`tests/`, `scripts/`, and config files.
