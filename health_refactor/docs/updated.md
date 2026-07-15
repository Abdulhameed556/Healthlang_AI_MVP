# SupportOs Backend — Monorepo Architecture

This document describes the current state of the `SupportOs-backend` monorepo: two independent
FastAPI services (**admin** and **backend**) that share one process but keep their concerns
fully separated at every layer.

---

## Repository layout

```
SupportOs-backend/
├── admin/                    # Admin panel service
│   ├── src/                  #   source code (presentation → domain)
│   └── scripts/              #   one-off scripts (e.g. seed_initial_admin.py)
├── backend/                  # Product SPA backend service
│   └── src/                  #   source code (presentation → domain)
├── tests/
│   ├── admin_tests/          # Admin unit / integration / e2e tests
│   └── backend_tests/        # Backend unit / integration / e2e tests
├── docs/
│   ├── admin_docs/           # Admin API + architecture documentation
│   ├── backend_docs/         # Backend API + architecture documentation
│   └── updated.md            # This file
├── run.py                    # Single entrypoint — mounts both services
├── requirements.txt          # Shared Python dependencies
└── Makefile                  # Dev commands
```

---

## How the two services are joined (`run.py`)

Both services expose independent `FastAPI()` instances and are combined via
`include_router` (not `mount`) into a single root app:

```python
# run.py (simplified)
from admin.src.presentation.api.app import admin_app
from backend.src.presentation.api.app import backend_app

app = FastAPI()
app.include_router(admin_app.router, prefix="/admin")
app.include_router(backend_app.router)
```

Result: one process, one port (`8000`), one Swagger UI at `/docs` — but two distinct
router hierarchies with separate middleware, auth schemes, and error handlers.

Swagger shows two security schemes side-by-side:
- **AdminAuth** — HMAC-signed JWT verified with `ADMIN_JWT_SECRET_KEY`
- **BackendAuth** — HMAC-signed JWT verified with `JWT_SECRET_KEY`

---

## Separation of concerns

| Concern | Admin service | Backend service |
|---------|--------------|-----------------|
| Source root | `admin/src/` | `backend/src/` |
| JWT secret env var | `ADMIN_JWT_SECRET_KEY` | `JWT_SECRET_KEY` |
| Database tables | `admin_users`, `admin_sessions`, `admin_invitations` | `organizations`, `users`, `invitations`, `user_sessions` |
| Who it serves | Internal staff / operators | Customer organizations and their users |
| Auth model | Invite-only; seeded initial super-admin | Invite-only; admin provisions org + super-admin |
| RBAC | `super_admin`, `admin`, `read_only` (server-side) | `super_admin`, `admin`, `read_only` (scoped to org) |
| Refresh tokens | Yes (`JWT_REFRESH_TOKEN_EXPIRE_DAYS`, default 3 days) | Yes (`JWT_REFRESH_TOKEN_EXPIRE_DAYS`, default 3 days) |
| Google OAuth | Optional (`GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`) | Optional (same env vars) |
| Internal API key | `ADMIN_INTERNAL_API_KEY` guards server-to-server calls | Accepts calls from admin via `X-Admin-Api-Key` |

Both services read the same `DATABASE_URL` — one Postgres database, separate table namespaces.

---

## Shared database, separate table namespaces

```
Postgres (DATABASE_URL)
├── admin_users            — admin panel staff accounts
├── admin_sessions         — admin JWT sessions
├── admin_invitations      — admin invite tokens
├── organizations          — customer orgs provisioned by admin
├── users                  — org members (multi-org: one row per org per email)
├── invitations            — pending org member invites
└── user_sessions          — backend JWT + refresh token sessions
```

A user email can appear in **multiple rows** in the `users` table — one per
`organization_id`. This is the multi-org membership model: the same person can
be a member of separate organizations with different roles. Login resolves the
correct user row by email + organization context.

---

## Authentication flows

### Backend login (`POST /api/v1/auth/login`)

1. `list_by_email` — load all user rows for the email across orgs.
2. `resolve_user_for_password_login` — verify password and pick the active row.
3. `build_user_session` — returns `(access_token, refresh_token, session)`.
4. Persist session; return both tokens plus `role`.

### Admin login (`POST /api/v1/auth/login` on admin router)

Same shape: invite-only, email/password or Google OAuth, returns both tokens.
Admin JWT uses `ADMIN_JWT_SECRET_KEY` so backend tokens cannot be replayed.

### Refresh (`POST /api/v1/auth/refresh`)

Public route. Exchanges a valid `refresh_token` for a new access JWT and a
rotated refresh token. Previous refresh token is invalidated immediately.

### Logout (`POST /api/v1/auth/logout`)

Sets `invalidated_at` on the session row. Subsequent requests with that token
are rejected even if the JWT has not technically expired.

---

## B2B invite-only provisioning

No public self-signup exists anywhere in the system.

```
Admin panel operator
  └─► POST /api/v1/internal/admin/create-invited-user
        (X-Admin-Api-Key)
        creates: organization (status=invited)
                 user (status=invited, role=super_admin)
                 invitation (status=pending, token=<url-safe>)
                 sends invite email
  └─► Invitee clicks link → frontend calls POST /api/v1/auth/login
        (is_new: true, invitation_token: ..., password: ...)
        activates: user status=active, org status=active
        returns: access_token + refresh_token
  └─► Org super_admin invites teammates
        POST /api/v1/organizations/invite-user
        (same invitation flow, smaller scope)
```

---

## Test structure

Tests mirror the source layout exactly:

```
tests/
├── admin_tests/
│   └── unit/
│       ├── application/   — use-case tests (mocked repos)
│       └── presentation/  — endpoint tests (TestClient)
└── backend_tests/
    └── unit/
        ├── application/   — use-case tests (mocked repos)
        └── presentation/  — endpoint tests (TestClient)
```

Run all unit tests:

```bash
pytest tests/admin_tests/unit tests/backend_tests/unit -q
```

Integration and e2e tests require a live database (`DATABASE_URL` must point to
a real Postgres instance):

```bash
pytest tests/ -q
```

---

## Key environment variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | both | Postgres connection string |
| `JWT_SECRET_KEY` | backend | Signs/verifies backend access tokens |
| `ADMIN_JWT_SECRET_KEY` | admin | Signs/verifies admin access tokens |
| `ADMIN_INTERNAL_API_KEY` | both | Server-to-server guard (empty = disabled) |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | both | Access token TTL (default 60) |
| `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | both | Refresh token TTL (default 3) |
| `GOOGLE_CLIENT_ID` | both | Google OAuth app ID |
| `GOOGLE_CLIENT_SECRET` | both | Google OAuth secret |
| `MAILGUN_API_KEY` | both | Email delivery |
| `MAILGUN_DOMAIN` | both | Sending domain |
| `SEED_ADMIN_EMAIL` | admin | Initial super-admin email (seeding) |
| `SEED_ADMIN_PASSWORD` | admin | Initial super-admin password (seeding) |

See [`.env.example`](../.env.example) for the full list.

---

## Related docs

- [Admin API reference](admin_docs/api/README.md)
- [Backend API reference](backend_docs/api/README.md)
- [Admin architecture](admin_docs/architecture/overview.md)
- [Backend architecture](backend_docs/architecture/overview.md)
- [Git workflow — admin](admin_docs/git-workflow.md)
- [Git workflow — backend](backend_docs/git-workflow.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
