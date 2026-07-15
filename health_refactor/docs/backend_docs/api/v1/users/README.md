# Users API (`/api/v1/users`)

JWT-protected routes for the signed-in product user.

Send `Authorization: Bearer <access_token>` on every call. Obtain the token from
[login](../auth/login.md) or [Google login](../auth/google-login.md).

For multi-org accounts, see [organization context](../auth/organization-context.md).

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [me.md](me.md) | GET | `/api/v1/users/me` | All roles |
| [list-organizations.md](list-organizations.md) | GET | `/api/v1/users/me/organizations` | All roles |
