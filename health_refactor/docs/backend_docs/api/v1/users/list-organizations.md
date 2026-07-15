# GET /api/v1/users/me/organizations

## URL

**Path:** `/api/v1/users/me/organizations`

**Full URL:** `<base>/api/v1/users/me/organizations`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/users/me/organizations` |

**See also:** [users README](README.md) · [organization context](../auth/organization-context.md) · [me.md](me.md)

## Summary

Returns every **active** organization membership for the authenticated user's email.
Use the response to build an org switcher in the SPA. After the user picks an org, send
`X-Organization-Id` on other JWT routes — see
[organization-context.md](../auth/organization-context.md).

This route lists **all** memberships; it is not scoped by `X-Organization-Id`.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Response (200)

```json
{
  "message": "Organizations retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "organizations": [
      {
        "organization_id": "550e8400-e29b-41d4-a716-446655440001",
        "organization_name": "Acme Corp",
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "role": "admin"
      },
      {
        "organization_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "organization_name": "Beta LLC",
        "user_id": "a50e8400-e29b-41d4-a716-446655440099",
        "role": "read_only"
      }
    ]
  }
}
```

| Field | Description |
|-------|-------------|
| `organization_id` | Tenant UUID — use as `X-Organization-Id` when switching |
| `organization_name` | Display name for the org switcher |
| `user_id` | User row id **in that org** (differs per membership) |
| `role` | Caller's role in that org (`super_admin`, `admin`, `read_only`) |

Results are ordered by membership `updated_at` (most recently updated first).
Invited or suspended memberships are omitted. If an org row is missing, that membership
is skipped.

## Errors

| Status | When |
|--------|------|
| 401 | Missing, expired, or revoked JWT |
| 403 | Account not active |

## Frontend notes

1. Call after login (or on app load) to refresh the org switcher — login also returns
   `organizations` with id and name; this endpoint adds `user_id` and `role` per org.
2. Default selection: org from login, or the first item if you prefer.
3. On switch, set `X-Organization-Id` on the API client; you do not need to log in again.
4. `user_id` in each item is the membership-specific id — use `organization_id` for tenant context.

## Related

- [organization-context.md](../auth/organization-context.md) — `X-Organization-Id` header
- [me.md](me.md) — profile for the **current** org context
- Code: `backend/src/presentation/api/v1/users/endpoints/list_user_organizations.py`
- Use-case: `backend/src/application/users/use_cases/list_user_organizations.py`
