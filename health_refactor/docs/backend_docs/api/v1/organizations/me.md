# GET /api/v1/organizations/me

## URL

**Path:** `/api/v1/organizations/me`

**Full URL:** `<base>/api/v1/organizations/me`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/organizations/me` |

## Summary

Returns the **organization profile** for the tenant tied to the authenticated user's JWT session.
All roles may call this route.

**See also:** [organizations README](README.md) · [update-profile.md](update-profile.md) · [users.md](users.md) · [invite-user.md](invite-user.md)

## Auth

```http
Authorization: Bearer <access_token>
```

## Response (200)

```json
{
  "message": "Organization profile retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Acme Corp",
    "industry": "fintech",
    "description": "Enterprise support platform",
    "size": "11-50",
    "status": "active"
  }
}
```

| Field | Description |
|-------|-------------|
| `organization_id` | Tenant UUID for this session |
| `name` | Organization display name |
| `industry` | Industry label |
| `description` | Optional blurb |
| `size` | Optional size band (read-only here) |
| `status` | `invited`, `active`, or `disabled` |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | Account not active |
| 404 | Organization not found |

## Code

- Endpoint: `admin/src/presentation/api/v1/organizations/endpoints/me.py`
- Use-case: `admin/src/application/organizations/use_cases/get_organization_profile.py`
