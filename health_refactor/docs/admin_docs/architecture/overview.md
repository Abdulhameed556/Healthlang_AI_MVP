# Admin Panel Backend — Architecture Overview

## Layers

| Layer | Package | Responsibility |
|---|---|---|
| Presentation | `admin/src/presentation/` | HTTP routing, RBAC deps, schemas |
| Application | `admin/src/application/` | Use-cases, orchestration |
| Domain | `admin/src/domain/` | Entities, value objects, repo interfaces |
| Infrastructure | `admin/src/infrastructure/` | DB, email, Redis, backend HTTP client |

## Isolation diagram

```
┌─────────────────────────────────────┐
│         Admin Panel Backend          │
│  port 8002 | DB: admin_panel         │
│  JWT secret: ADMIN_OWN_SECRET        │
│                                      │
│  Tables:                             │
│    admin_users                       │
│    admin_sessions                    │
│    admin_invitations                 │
└──────────────┬──────────────────────┘
               │ internal HTTP (read org data,
               │ create org, enable/disable org)
               ▼
┌─────────────────────────────────────┐
│         Backend Service             │
│  port 8000 | DB: dashboard          │
│  JWT secret: BACKEND_SECRET         │
└─────────────────────────────────────┘
```

The admin service **never** connects to the backend database directly.
All product data is read/written through the backend's internal API.
