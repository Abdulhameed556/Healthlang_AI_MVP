# POST /api/v1/internal/admin/users

## URL

**Path:** `/api/v1/internal/admin/users`

**Full URL:** `<base>/api/v1/internal/admin/users`

`<base>` is the product backend origin (scheme + host + port), **no trailing slash**.

| Environment | Base URL (`<base>`) | Example full URL |
|-------------|---------------------|------------------|
| Local | `http://localhost:8000` | `http://localhost:8000/api/v1/internal/admin/users` |
| Staging | `https://api-staging.example.com` | `https://api-staging.example.com/api/v1/internal/admin/users` |
| Production | `https://api.example.com` | `https://api.example.com/api/v1/internal/admin/users` |

Replace `<base>` with the value your Admin Portal backend is configured to call.

## Summary

Admin Portal provisions a new organization and invited super-admin user, creates a
pending invitation, and sends an invitation email. Server-to-server only (API key).

## Auth

- Required: yes
- Header: `X-Admin-Api-Key: <ADMIN_INTERNAL_API_KEY>` or `Authorization: Bearer <key>`
- Product JWT: not used

## Request

- Content-Type: `application/json`

```json
{
  "email": "admin@acme.com",
  "organization_name": "Acme Corp",
  "industry": "fintech",
  "first_name": "Ada",
  "last_name": "Lovelace",
  "description": "Optional org description",
  "organization_size": "11-50"
}
```

## Response

### 201 Created

```json
{
  "message": "Invited user created successfully",
  "status_code": 201,
  "error": false,
  "data": {
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "550e8400-e29b-41d4-a716-446655440001",
    "invitation_id": "550e8400-e29b-41d4-a716-446655440002",
    "invitation_link": "https://app.example.com/invitations/accept?token=..."
  }
}
```

### Error responses

| Status | When | Sample `message` | `data` |
|--------|------|------------------|--------|
| 401 | Missing/invalid API key | `Invalid or missing admin API key` | `null` |
| 409 | Email already registered | Conflict message from server | `null` |
| 409 | Pending invitation exists | Conflict message from server | `null` |
| 422 | Invalid body | `Validation failed` | `{ "errors": [...] }` |

Error envelope:

```json
{
  "message": "A user with email admin@acme.com already exists",
  "status_code": 409,
  "error": true,
  "data": null
}
```

## Frontend notes

- **Admin app only** — do not call from the product SPA; use Admin backend proxy if needed.
- Store `invitation_link` from `data` for support/debug; the invitee receives it by email.
- The raw invitation token is **not** returned in the API response (only embedded in `invitation_link`).

### Local development (`APP_ENV=development`)

Invitation emails are **not sent** by default. Use `data.invitation_link` from this
response (or the `invitation_email: skipped` log line) to open the accept flow in the
product SPA. The link contains the token query param; acceptance works without email.

To test real email delivery locally, set `SEND_INVITATION_EMAIL_IN_DEV=true`.

## Related

- Code: `backend/src/presentation/api/v1/internal/admin/endpoints/create_invited_user.py`
- Use-case: `backend/src/application/users/use_cases/create_invited_user_from_admin.py`
- `CONTRIBUTING.md` — application layout and email providers
