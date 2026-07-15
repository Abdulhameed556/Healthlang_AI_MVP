# Auth API (`/admin/api/v1/auth`)

Admin Panel authentication. Login is a **two-step email + password + OTP** flow.
Sessions are **60 minutes** with **no refresh token**. There is no Google OAuth on
the admin side.

| Doc | Method | Path | Auth |
|-----|--------|------|------|
| [login.md](login.md) | POST | `/admin/api/v1/auth/login/initiate` | — |
| [login.md](login.md) | POST | `/admin/api/v1/auth/login/verify` | — |
| [logout.md](logout.md) | POST | `/admin/api/v1/auth/logout` | Bearer JWT |

**Planned** (not wired yet): `/auth/invitations/{token}/accept`, `/auth/password/change`.

## Protected routes (JWT required)

After login, send `Authorization: Bearer <access_token>`:

| Module | README |
|--------|--------|
| Users | [../users/README.md](../users/README.md) |
| Organizations | [../organizations/README.md](../organizations/README.md) |
