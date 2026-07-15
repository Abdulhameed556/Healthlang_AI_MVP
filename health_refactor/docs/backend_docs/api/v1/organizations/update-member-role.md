# PATCH /api/v1/organizations/users/{user_id}/role

## URL

**Path:** `/api/v1/organizations/users/{user_id}/role`

**Full URL:** `<base>/api/v1/organizations/users/{user_id}/role`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/organizations/users/550e8400-e29b-41d4-a716-446655440000/role` |

**See also:** [organizations README](README.md) · [users.md](users.md) · [remove-member.md](remove-member.md)

## Summary

Changes a member's organization role. Requires `super_admin` or `admin`.

| Actor | Can change | Can assign |
|-------|------------|------------|
| `super_admin` | Any member except themselves | `super_admin`, `admin`, `read_only` |
| `admin` | `admin` and `read_only` only | `admin`, `read_only` |

## Auth

```http
Authorization: Bearer <access_token>
```

## Path parameters

| Name | Type | Description |
|------|------|-------------|
| `user_id` | UUID | Member whose role will change |

## Request

```json
{
  "role": "read_only"
}
```

| Field | Required | Values |
|-------|----------|--------|
| `role` | yes | `super_admin` (super_admin only), `admin`, `read_only` |

## Response (200)

```json
{
  "message": "Organization member role updated successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "ada@acme.com",
    "first_name": "Ada",
    "last_name": "Lovelace",
    "role": "read_only",
    "status": "active"
  }
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller, self role change, or admin targeting `super_admin` |
| 404 | Member not found in caller's org |
| 422 | Invalid role value |

## Code

- Endpoint: `admin/src/presentation/api/v1/organizations/endpoints/users.py`
- Use-case: `admin/src/application/organizations/use_cases/update_user_role.py`
