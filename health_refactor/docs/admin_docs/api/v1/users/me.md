# GET /admin/api/v1/users/me

## URL

**Path:** `/admin/api/v1/users/me`

**Full URL:** `<base>/admin/api/v1/users/me`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/admin/api/v1/users/me` |

**See also:** [users README](README.md) · [login.md](../auth/login.md)

## Summary

Returns the **authenticated admin's own profile**. Both `admin` and `read_only`
roles may call it — it only ever returns the caller's own record.

Admin users are **not** tied to an organization, so there is no `organization_id`
(that's a product/backend concept, not an admin-panel one).

## Auth

```http
Authorization: Bearer <access_token>
```

The access token comes from [`/login/verify`](../auth/login.md). Admin sessions are
60 minutes, no refresh token.

| Role | Can call |
|------|----------|
| `admin` | yes |
| `read_only` | yes |

## Response (200)

The profile object is returned **directly** — admin success responses are not
wrapped in an envelope:

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "ada@admin.com",
  "first_name": "Ada",
  "last_name": "Min",
  "role": "admin",
  "status": "active",
  "must_change_password": false
}
```

| Field | Description |
|-------|-------------|
| `user_id` | The admin's UUID |
| `email` | Login email |
| `first_name` / `last_name` | Display name |
| `role` | `admin` or `read_only` |
| `status` | `pending`, `active`, or `locked` |
| `must_change_password` | `true` if the admin should change their password (flag only; not enforced yet) |

The password hash and other internal fields are never returned.

## Errors

| Status | When |
|--------|------|
| 401 | Missing/invalid `Authorization` header, expired/revoked session, or inactive account |

## Frontend notes

- Call right after `/login/verify` to populate the admin shell (name, role).
- Use `role` to gate write actions in the UI (`read_only` cannot perform writes; the server also enforces this).
- `must_change_password` is returned for future use; no forced-change flow is wired yet.

## Code

- Endpoint: `admin/src/presentation/api/v1/users/endpoints/me.py`
- Auth guard: `admin/src/application/auth/dependencies.py` (`get_current_admin`)
