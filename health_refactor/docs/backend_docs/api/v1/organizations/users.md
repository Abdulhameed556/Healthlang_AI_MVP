# GET /api/v1/organizations/users

## URL

**Path:** `/api/v1/organizations/users`

**Full URL:** `<base>/api/v1/organizations/users`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/organizations/users` |

## Summary

Returns a **paginated** list of **active** and **invited** members of the caller's organization
with email, role, and name. Requires `super_admin` or `admin`. `read_only` receives **403**.

**See also:** [organizations README](README.md) · [invite-user.md](invite-user.md) · [remove-member.md](remove-member.md) · [update-member-role.md](update-member-role.md) · [me.md](me.md)

Suspended and declined users are excluded.

## Auth

```http
Authorization: Bearer <access_token>
```

## Query parameters

| Param | Type | Default | Limits | Description |
|-------|------|---------|--------|-------------|
| `page` | integer | `1` | ≥ 1 | Page number (1-based) |
| `page_size` | integer | `20` | 1–100 | Members per page |

**Example:** `GET /api/v1/organizations/users?page=1&page_size=20`

## Response (200)

```json
{
  "message": "Organization members retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "users": [
      {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "admin@acme.com",
        "first_name": "Ada",
        "last_name": "Lovelace",
        "role": "super_admin",
        "status": "active"
      },
      {
        "user_id": "550e8400-e29b-41d4-a716-446655440001",
        "email": "teammate@acme.com",
        "first_name": "Grace",
        "last_name": "Hopper",
        "role": "read_only",
        "status": "invited"
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### Pagination fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total active and invited members |
| `page` | integer | Current page |
| `page_size` | integer | Page size used |
| `total_pages` | integer | `0` when `total` is `0` |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 422 | Invalid query parameter (e.g. `page=0`) |

## Frontend notes

- Default to `page=1` and `page_size=20`; expose page size up to 100.
- Use `total_pages` for pagination UI.

## Code

- Endpoint: `backend/src/presentation/api/v1/organizations/endpoints/users.py`
- Use-case: `backend/src/application/organizations/use_cases/list_organization_users.py`
