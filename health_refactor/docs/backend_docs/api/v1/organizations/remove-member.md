# DELETE /api/v1/organizations/users/{user_id}

## URL

**Path:** `/api/v1/organizations/users/{user_id}`

**Full URL:** `<base>/api/v1/organizations/users/{user_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/organizations/users/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [organizations README](README.md) · [users.md](users.md) · [update-member-role.md](update-member-role.md)

## Summary

Removes a member from the caller's organization by setting their status to `suspended`,
invalidating all active sessions, and expiring any pending invitation for that email.

Requires `super_admin` or `admin`.

| Actor | Can remove |
|-------|------------|
| `super_admin` | Any member except themselves |
| `admin` | `admin` and `read_only` only (not `super_admin`) |

## Auth

```http
Authorization: Bearer <access_token>
```

## Path parameters

| Name | Type | Description |
|------|------|-------------|
| `user_id` | UUID | Member to remove |

## Response (200)

```json
{
  "message": "Organization member removed successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller, self-removal, or admin targeting `super_admin` |
| 404 | Member not found in caller's org, or already suspended |

Removed members may be invited again later (`POST /organizations/users/invite`).

## Code

- Endpoint: `admin/src/presentation/api/v1/organizations/endpoints/users.py`
- Use-case: `admin/src/application/organizations/use_cases/remove_organization_member.py`
