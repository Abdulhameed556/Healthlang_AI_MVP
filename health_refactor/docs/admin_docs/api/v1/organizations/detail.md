# GET /admin/api/v1/organizations/{org_id}

## URL

**Path:** `/admin/api/v1/organizations/{org_id}`

**Full URL (local):** `http://localhost:8000/admin/api/v1/organizations/{org_id}`

**See also:** [organizations README](README.md) · [list.md](list.md)

## Summary

**Admin-only.** Returns full details for a single organization, including
industry, description, size, activation status, total agent count, and the
complete list of users (email, name, role).

Requires the **`admin`** role; `read_only` admins are rejected with 403.

## Auth

```http
Authorization: Bearer <access_token>
```

## Path parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `org_id` | UUID | The organization's unique ID |

## Request

No body.

## Response (200)

```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Acme Corp",
  "industry": "Technology",
  "description": "AI-powered customer support platform",
  "size": "50-200",
  "status": "active",
  "onboarded_at": "2024-01-15T10:30:00Z",
  "onboarded_by": "admin_panel",
  "users": [
    {
      "email": "john.doe@acme.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": "super_admin"
    },
    {
      "email": "jane.smith@acme.com",
      "first_name": "Jane",
      "last_name": "Smith",
      "role": "admin"
    }
  ]
}
```

| Field | Description |
|-------|-------------|
| `id` | Organization UUID |
| `name` | Organization display name |
| `industry` | Industry sector |
| `description` | Optional organization description (`null` if not set) |
| `size` | Optional size band e.g. `50-200` (`null` if not set) |
| `status` | `active`, `pending`, or `disabled` |
| `onboarded_at` | ISO 8601 onboard timestamp |
| `onboarded_by` | `admin_panel` or `self_service` (`null` if not set) |
| `users` | All users in the org ordered by creation date |
| `users[].email` | User email address |
| `users[].first_name` | User first name |
| `users[].last_name` | User last name |
| `users[].role` | `super_admin`, `admin`, `manager`, or `read_only` |

## Errors

| Status | When |
|--------|------|
| 401 | Missing/invalid admin Bearer token |
| 403 | Caller is `read_only` (not an admin) |
| 404 | No organization found with this `org_id` |

## Code

- Endpoint: `admin/src/presentation/api/v1/organizations/endpoints/detail.py`
- Use-case: `admin/src/application/organizations/use_cases/get_organization_detail.py`
