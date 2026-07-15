# Auth API (`/api/v1/auth`)

Product SPA authentication. Login, refresh, and password reset routes are **public**;
logout requires the current JWT. Successful login returns a JWT in `data.access_token`,
a `data.refresh_token`, and `data.organizations` (active org id + name list for the
user's email).

| Doc | Method | Path | Auth |
|-----|--------|------|------|
| [login.md](login.md) | POST | `/api/v1/auth/login` | — |
| [google-url.md](google-url.md) | GET | `/api/v1/auth/google/url` | — |
| [google-login.md](google-login.md) | POST | `/api/v1/auth/google` | — |
| [password-reset-request.md](password-reset-request.md) | POST | `/api/v1/auth/password-reset/request` | — |
| [password-reset-complete.md](password-reset-complete.md) | POST | `/api/v1/auth/password-reset/complete` | — |
| [logout.md](logout.md) | POST | `/api/v1/auth/logout` | Bearer JWT |
| [refresh.md](refresh.md) | POST | `/api/v1/auth/refresh` | — |

**Not implemented yet** (no docs): `/auth/register`.

Invitation **decline:** [../invitations/decline.md](../invitations/decline.md).
Invitation **acceptance** uses login with `is_new: true` (email or Google), not a separate accept route.

## Protected routes (JWT required)

After login, use `Authorization: Bearer <access_token>` on every private product route.

Users in **multiple organizations** can optionally send
`X-Organization-Id: <uuid>` to scope the request to another active membership without
re-login. See [organization-context.md](organization-context.md).

| Doc | Topic |
|-----|--------|
| [organization-context.md](organization-context.md) | Multi-org header on JWT routes |
| [logout.md](logout.md) | Invalidate current session |

| Module | README |
|--------|--------|
| Users | [../users/README.md](../users/README.md) |
