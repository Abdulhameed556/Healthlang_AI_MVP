# POST /api/v1/organizations/users/invite

## URL

**Path:** `/api/v1/organizations/users/invite`

**Full URL:** `<base>/api/v1/organizations/users/invite`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/organizations/users/invite` |

**See also:** [organizations README](README.md) · [users.md](users.md) (list members) · [update-profile.md](update-profile.md)

## Summary

Logged-in `super_admin` or `admin` invites a teammate into their organization. The invitee
activates via the same flow as Admin Portal invites: [login](../auth/login.md) or
[Google login](../auth/google-login.md) with `is_new: true`.

## Auth

```http
Authorization: Bearer <access_token>
```

Obtain `access_token` from `POST /api/v1/auth/login` or `POST /api/v1/auth/google`.

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | no (403) |

## Request body

```json
{
  "email": "teammate@acme.com",
  "role": "admin",
  "first_name": "Ada",
  "last_name": "Lovelace"
}
```

| Field | Required | Notes |
|-------|----------|--------|
| `email` | yes | Normalized to lowercase |
| `role` | yes | `admin` or `read_only` only |
| `first_name` | no | Placeholder until accept if omitted |
| `last_name` | no | Placeholder until accept if omitted |

## Success (201)

```json
{
  "message": "Invitation sent successfully",
  "status_code": 201,
  "error": false,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "invitation_id": "550e8400-e29b-41d4-a716-446655440001",
    "email": "teammate@acme.com",
    "role": "admin",
    "invitation_link": "http://localhost:3000/invitations/accept?token=..."
  }
}
```

In `APP_ENV=development`, email may be skipped; use `invitation_link` from `data`.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Organization not found |
| 409 | User already **active in this org** |

Same email in **another** organization is allowed — each org has its own user row (`email` + `organization_id` unique).

Re-inviting the same email while a pending invitation still exists **supersedes** the old invite: the previous row is marked `expired` and a new invitation is created (new token + email).

| 422 | Invalid email or role |
| 503 | Email provider failure (after DB commit) |

## Frontend flow

1. User logs in → store `access_token`.
2. `POST /organizations/users/invite` with Bearer token + `email` + `role`.
3. Invitee opens `invitation_link` → accept via auth endpoints with `is_new: true`.

## Code

- Endpoint: `admin/src/presentation/api/v1/organizations/endpoints/invite.py`
- Use-case: `admin/src/application/organizations/use_cases/invite_user.py`
