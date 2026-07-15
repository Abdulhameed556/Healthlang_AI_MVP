# GET /api/v1/users/me

## URL

**Path:** `/api/v1/users/me`

**Full URL:** `<base>/api/v1/users/me`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/users/me` |

**See also:** [users README](README.md) · [list-organizations.md](list-organizations.md) · [organization context](../auth/organization-context.md)

## Summary

Returns the **authenticated user's profile** for the **current organization context**
(login session org, or the org selected via `X-Organization-Id`). All roles may call this
route.

Use [list-organizations.md](list-organizations.md) for the full org switcher list (all
memberships). Use this route for display name, role, and status in the **active** tenant.

## Auth

```http
Authorization: Bearer <access_token>
```

Optional `X-Organization-Id: <uuid>` selects which membership row is returned when the user
belongs to multiple orgs — see [organization-context.md](../auth/organization-context.md).

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Response (200)

```json
{
  "message": "Profile retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "organization_id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "admin@acme.com",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "role": "admin",
    "status": "active",
    "auth_method": "email_password"
  }
}
```

| Field | Description |
|-------|-------------|
| `user_id` | Membership row id in the **active** org |
| `organization_id` | Active tenant UUID (matches `X-Organization-Id` when set) |
| `email` | Same across all org memberships |
| `role` | Role in the **active** org |
| `status` | Account status in the **active** org |
| `auth_method` | `email_password` or `google_oauth` |

Password hashes and session tokens are never returned.

## Errors

| Status | When |
|--------|------|
| 401 | Missing, expired, or revoked JWT |
| 403 | Account not active, invalid org header, or no access to requested org |
| 404 | User not found |

## Frontend notes

- Call after login to show the user shell for the default org.
- After org switch, send `X-Organization-Id` and call again to refresh name/role for that tenant.
- `user_id` changes per org membership; `email` stays the same.

## Related

- [list-organizations.md](list-organizations.md) — all org memberships
- [login.md](../auth/login.md) — obtain JWT
- Code: `backend/src/presentation/api/v1/users/endpoints/me.py`
- Use-case: `backend/src/application/users/use_cases/get_current_user_profile.py`
