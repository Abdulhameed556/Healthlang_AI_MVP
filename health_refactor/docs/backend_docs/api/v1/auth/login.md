# POST /api/v1/auth/login

## URL

**Path:** `/api/v1/auth/login`

**Full URL:** `<base>/api/v1/auth/login`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/auth/login` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/auth/login` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/auth/login` |

## Summary

Email/password login for **active** users, or **invitation activation** when the invitee
sets a password from the invite link (`is_new: true`). On success, returns a JWT and
creates a `user_sessions` row.

## Auth

- Required: no
- Product JWT: not used on this request; returned in `data.access_token` on success

## Request

- Content-Type: `application/json`

### Normal login (`is_new: false`)

```json
{
  "email": "admin@acme.com",
  "password": "Sam@123456",
  "is_new": false
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `email` | yes | Must match an active user |
| `password` | yes | Min 8 characters |
| `is_new` | no | Default `false` |

### Invitation activation (`is_new: true`)

```json
{
  "password": "Sam@123456",
  "is_new": true,
  "invitation_token": "url-safe-token-from-invite-link"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `invitation_token` | yes | From invite email / link query param |
| `password` | yes | Min 8 characters; stored as bcrypt hash |
| `email` | no | If sent, must match the invitation email |
| `is_new` | yes | Must be `true` |

## Response

### 200 OK

```json
{
  "message": "Login successful",
  "status_code": 200,
  "error": false,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "opaque-refresh-token",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "admin@acme.com",
    "role": "read_only",
    "organizations": [
      {
        "organization_id": "550e8400-e29b-41d4-a716-446655440001",
        "organization_name": "Acme Corp"
      },
      {
        "organization_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
        "organization_name": "Beta LLC"
      }
    ],
    "activated_invitation": false
  }
}
```

| Field | Description |
|-------|-------------|
| `access_token` | JWT; send as `Authorization: Bearer <token>` on protected routes |
| `refresh_token` | Opaque token; exchange via `POST /auth/refresh` when access token expires |
| `user_id` | Membership row id for the org used at login (JWT session) |
| `role` | User's role in the org used at login (`super_admin`, `admin`, `read_only`) |
| `organizations` | Active orgs for this email (`organization_id`, `organization_name`); use for org switcher |
| `activated_invitation` | `true` when this call completed invite acceptance |

There is **no** top-level `organization_id` on login responses.

The JWT session is tied to `user_id` (one membership). For another org, send
`X-Organization-Id` without re-login — see [organization-context.md](organization-context.md).
For roles per org, use [../users/list-organizations.md](../users/list-organizations.md).

Access token TTL: **60 minutes** (`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`).
Refresh token TTL: **3 days** (`JWT_REFRESH_TOKEN_EXPIRE_DAYS`).

### Error responses

| Status | When | Sample `message` |
|--------|------|------------------|
| 401 | Wrong email/password, unknown user, invalid invite | `Invalid email or password` |
| 401 | User still `invited` on normal login | `Complete your invitation first using the link from your email` |
| 403 | User not active (e.g. suspended) | `Account is not active` |
| 422 | Body validation (missing email, token, short password) | `Validation failed` |
| 422 | Email does not match invitation | `Email does not match this invitation` |
| 503 | Database unavailable | `Database temporarily unavailable. Please retry.` |

Validation error envelope:

```json
{
  "message": "Validation failed",
  "status_code": 422,
  "error": true,
  "data": {
    "errors": [
      {
        "type": "value_error",
        "loc": ["body"],
        "msg": "Value error, email is required when is_new is false"
      }
    ]
  }
}
```

## Frontend notes

- **Invite flow:** parse `token` from the invite URL, call with `is_new: true` + `invitation_token` + chosen password.
- **Returning users:** `is_new: false` with `email` + `password`.
- Store both `data.access_token` and `data.refresh_token` (memory or secure storage).
- Build the org switcher from `data.organizations` (or refresh via
  [../users/list-organizations.md](../users/list-organizations.md)).
- Attach `access_token` to API calls as `Authorization: Bearer <token>`.
- If the user switches org, send optional `X-Organization-Id` on protected routes — see
  [organization-context.md](organization-context.md).
- When a protected route returns **401**, call [refresh.md](refresh.md) to get new tokens silently.
- On logout, call [logout.md](logout.md) to invalidate the session server-side.
- Google alternative: see [google-login.md](google-login.md) with `is_new: true`.

## Related

- [google-login.md](google-login.md) — same `LoginResponse` shape via Google OAuth
- Admin provision: [../internal/admin/create-invited-user.md](../internal/admin/create-invited-user.md)
- Code: `backend/src/presentation/api/v1/auth/endpoints/login.py`
- Use-case: `backend/src/application/auth/use_cases/login_with_email.py`
