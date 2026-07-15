# SupportOS AI API — Documentation

Frontend integration docs for the SupportOS AI backend API (`/api/v1`).

## Base URL

Every endpoint doc uses:

**`<base>/api/v1/...`**

| Piece | Meaning |
|-------|---------|
| `<base>` | Backend origin only — scheme + host + port, **no trailing slash** |
| Path | Always starts with `/api/v1/` |

| Environment | Typical `<base>` |
|-------------|------------------|
| Local | `http://localhost:8000` (see `APP_PORT` in `.env`) |
| Staging / Production | Your deployed API host (e.g. `https://api.example.com`) |

**Example:** health check → `<base>/api/v1/health` → locally `http://localhost:8000/api/v1/health`.

Admin internal routes: `<base>/api/v1/internal/admin/...`.

## Standard response envelope

Every JSON response uses the same top-level fields:

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Human-readable summary |
| `status_code` | number | Mirrors HTTP status (200, 201, 401, …) |
| `error` | boolean | `false` on success, `true` on failure |
| `data` | object \| null | Business payload on success; optional details on error |

**Success example:**

```json
{
  "message": "OK",
  "status_code": 200,
  "error": false,
  "data": { "status": "ok" }
}
```

**Error example:**

```json
{
  "message": "Invalid or missing admin API key",
  "status_code": 401,
  "error": true,
  "data": null
}
```

Read nested fields from **`data`**, not from the root. See `CONTRIBUTING.md` § Standard API response envelope.

## Multi-organization context (JWT routes)

The same email can be an active member of more than one organization. Protected routes
scope data to one org at a time.

| Header | Required | Purpose |
|--------|----------|---------|
| `Authorization: Bearer <access_token>` | yes | Session JWT from login or Google OAuth |
| `X-Organization-Id` | no | Active org UUID when the user switched tenant in the SPA |

If the header is omitted, the org from **login** is used. Invalid UUID or no membership
→ **403**. Full behavior: [v1/auth/organization-context.md](v1/auth/organization-context.md).

## Structure

```
docs/api/
├── README.md           ← you are here
├── endpoints.md        ← quick reference table (all routes)
└── v1/
    ├── auth/
    ├── users/
    ├── organizations/
    ├── internal/
    │   └── admin/      # Admin Portal → Backend (API key)
    ├── agents/
    ├── tickets/
    ├── dashboard/
    └── ...
```

Each implemented endpoint gets a file under `v1/<module>/` with sample
request/response payloads (including the envelope), auth requirements, and frontend notes.

**No endpoint docs are written until that route is implemented.**

See `../../.cursor/rules/api-documentation.mdc` and `CONTRIBUTING.md`.
