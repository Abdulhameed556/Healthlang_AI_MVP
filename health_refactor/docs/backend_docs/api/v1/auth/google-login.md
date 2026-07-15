# POST /api/v1/auth/google

## URL

**Path:** `/api/v1/auth/google`

**Full URL:** `<base>/api/v1/auth/google`

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/auth/google` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/auth/google` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/auth/google` |

## Summary

Exchange a Google authorization `code` for a JWT. Supports **invitation activation**
(`is_new: true`) and **returning user login** (`is_new: false`). Google email must
match the invited or existing account email. No public signup — unknown Google emails
are rejected.

## Auth

- Required: no
- Product JWT: returned in `data.access_token` on success

## Request

- Content-Type: `application/json`

### Returning user (`is_new: false`)

```json
{
  "code": "4/0AeanS...",
  "is_new": false
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `code` | yes | Authorization code from Google callback (single use, short-lived) |
| `is_new` | no | Default `false` |

### Invitation activation (`is_new: true`)

```json
{
  "code": "4/0AeanS...",
  "is_new": true,
  "invitation_token": "url-safe-token-from-invite-link"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `code` | yes | From Google callback |
| `invitation_token` | yes | From invite link |
| `is_new` | yes | Must be `true` |

Google account email must match the invitation email (case-normalized).

## Response

### 200 OK

Same shape as [login.md](login.md):

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
      }
    ],
    "activated_invitation": true
  }
}
```

| Field | Description |
|-------|-------------|
| `access_token` | JWT; send as `Authorization: Bearer <token>` on protected routes |
| `refresh_token` | Opaque token; exchange via [refresh.md](refresh.md) |
| `user_id` | Membership row id for the org used at login (JWT session) |
| `role` | User's role in the org used at login |
| `organizations` | Active orgs for this email (`organization_id`, `organization_name`) |
| `activated_invitation` | `true` when this call completed invite acceptance |

There is **no** top-level `organization_id` on login responses. Use `organizations` for the
org switcher; the JWT session is tied to `user_id`.

On invite acceptance via Google:

- User `status` → `active`, `auth_method` → `google_oauth`, no password stored
- Invitation → `accepted`, organization → `active` if it was `invited`

### Error responses

| Status | When | Sample `message` |
|--------|------|------------------|
| 401 | Invalid/expired Google `code` | `Failed to authenticate with Google` |
| 401 | No user for Google email | `No account found for this Google email` |
| 401 | User still `invited` on normal login | `Complete your invitation first using the link from your email` |
| 401 | Invalid invitation / user state | `Invalid invitation or user state` |
| 403 | User not active | `Account is not active` |
| 422 | Missing `invitation_token` when `is_new: true` | `Validation failed` |
| 422 | Google email ≠ invite email | `Email does not match this invitation` |
| 503 | Database unavailable | `Database temporarily unavailable. Please retry.` |

## Frontend notes

- **Full Google flow:**
  1. [google-url.md](google-url.md) — get `oauth_url` and redirect
  2. SPA callback receives `code`
  3. This endpoint with `code` (+ invite fields on accept page)
- **Invite page:** keep `invitation_token` from URL; pass `is_new: true`.
- **Security:** exchange `code` on the backend only; never send `GOOGLE_CLIENT_SECRET` to the browser.
- Users provisioned via Admin invite only; Google cannot create a new org/user without a prior invite.
- Build the org switcher from `data.organizations` (same shape as [login.md](login.md)).
- Multi-org: optional `X-Organization-Id` on protected routes — [organization-context.md](organization-context.md).
- Per-org `role` / `user_id`: [../users/list-organizations.md](../users/list-organizations.md).

## Related

- [google-url.md](google-url.md) — step 1 of OAuth flow
- [login.md](login.md) — email/password with same response shape
- Code: `backend/src/presentation/api/v1/auth/endpoints/google_oauth.py`
- Use-case: `backend/src/application/auth/use_cases/login_with_google.py`
