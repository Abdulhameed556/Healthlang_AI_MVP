# GET /admin/api/v1/organizations

## URL

**Path:** `/admin/api/v1/organizations`

**Full URL (local):** `http://localhost:8000/admin/api/v1/organizations`

**See also:** [organizations README](README.md) · [detail.md](detail.md)

## Summary

**Admin-only.** Returns all product organizations ordered by onboard date
(newest first), each with its activation status.

Status values:

| Value | Meaning |
|-------|---------|
| `active` | Organization has completed onboarding |
| `pending` | Organization has been invited but not yet activated |
| `disabled` | Organization has been disabled |

Requires the **`admin`** role; `read_only` admins are rejected with 403.

## Auth

```http
Authorization: Bearer <access_token>
```

## Request

No body. No query parameters.

## Response (200)

```json
{
  "organizations": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "name": "Acme Corp",
      "industry": "Technology",
      "status": "active",
      "onboarded_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "8d7a3b21-1234-4abc-9def-0123456789ab",
      "name": "Beta Inc",
      "industry": "Finance",
      "status": "pending",
      "onboarded_at": "2024-02-20T08:00:00Z"
    }
  ],
  "total": 2
}
```

| Field | Description |
|-------|-------------|
| `organizations` | Array of organization summaries |
| `organizations[].id` | Organization UUID |
| `organizations[].name` | Organization display name |
| `organizations[].industry` | Industry sector |
| `organizations[].status` | `active`, `pending`, or `disabled` |
| `organizations[].onboarded_at` | ISO 8601 onboard timestamp |
| `total` | Total count (equals `organizations.length`) |

## Errors

| Status | When |
|--------|------|
| 401 | Missing/invalid admin Bearer token |
| 403 | Caller is `read_only` (not an admin) |

## Code

- Endpoint: `admin/src/presentation/api/v1/organizations/endpoints/list.py`
- Use-case: `admin/src/application/organizations/use_cases/list_organizations.py`
