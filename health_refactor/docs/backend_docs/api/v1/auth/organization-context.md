# Organization context (`X-Organization-Id`)

## Summary

Product users can belong to **more than one organization** with the same email. Every
**JWT-protected** route (`Authorization: Bearer <access_token>`) scopes data to a single
organization.

By default, that organization is the one tied to the user row used at **login**. To work
in a different org without logging in again, send an optional header:

```http
Authorization: Bearer <access_token>
X-Organization-Id: <organization_uuid>
```

The backend resolves `auth.organization_id`, `auth.role`, and related checks from the
**active membership** for that org. Endpoint handlers do not change — they keep using
`auth.organization_id` as today.

## When to send the header

| Situation | Header |
|-----------|--------|
| User has one org, or you want the login org | Omit (recommended) |
| User switched org in the SPA and should see another tenant | Send target org UUID |
| Header matches login org | Omit or send same UUID (equivalent) |

Login always creates a session for the user row that authenticated (invite activation or
the membership chosen at login). The header only **re-targets** subsequent requests to
another active membership with the **same email**.

## Header rules

| Rule | Detail |
|------|--------|
| Name | `X-Organization-Id` |
| Value | UUID string (e.g. `550e8400-e29b-41d4-a716-446655440000`) |
| Required | No on any protected route |
| Whitespace | Trimmed before parse |

Invalid UUID → **403** with message `Invalid organization id header`.

## Access checks

When the header is present and differs from the login org:

1. Look up an **active** user row with the session email + requested `organization_id`.
2. If none → **403** with message `You do not have access to this organization`.
3. If found → `auth` uses that row’s `user_id`, `organization_id`, `email`, and `role`.

Suspended or invited memberships in the target org do not grant access.

## What does not change

| Topic | Behavior |
|-------|----------|
| JWT / session | Still validated as today; logout invalidates the session |
| `AuthContext` shape | `user_id`, `organization_id`, `email`, `role` |
| Public routes | No Bearer, no org header (login, refresh, password reset, etc.) |
| Admin routes | Admin API key / admin JWT — not product `X-Organization-Id` |

## Example request

```http
GET /api/v1/agents/ HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
X-Organization-Id: 7c9e6679-7425-40de-944b-e07fc1f90ae7
```

List/filter results (agents, org members, API tools, etc.) apply to org
`7c9e6679-7425-40de-944b-e07fc1f90ae7`, using the caller’s role in **that** org.

## Errors

| HTTP | When | Typical `message` |
|------|------|-------------------|
| 401 | Missing, expired, or revoked token | `Missing or invalid access token` / `Access token has expired` |
| 403 | Bad header UUID | `Invalid organization id header` |
| 403 | No active membership in requested org | `You do not have access to this organization` |
| 403 | Session user not active | `Account is not active` |

## Frontend notes

1. **Login** — store `access_token`, `refresh_token`, and `organizations` from the login
   response (id + name). Default tenant is the membership tied to `user_id` / JWT session.
2. **Org switcher** — persist the selected org id client-side; set `X-Organization-Id` on
   every API client request while that org is active.
3. **Omit when unnecessary** — if the selected org is the login org, you may omit the
   header.
4. **403 on switch** — show “no access” and fall back to a known-good org or re-prompt
   login; do not retry with the same header indefinitely.
5. **Refresh** — [refresh.md](refresh.md) does not take the org header; after refresh,
   keep sending the same `X-Organization-Id` on protected calls.
6. **Logout** — [logout.md](logout.md) invalidates the session; clear tokens and selected
   org state.

Listing all orgs for the signed-in email: [../users/list-organizations.md](../users/list-organizations.md)
(`GET /users/me/organizations`).

## Swagger / OpenAPI

Protected product routes show **BackendAuth** (Bearer JWT). The org header is optional
and is documented here; paste the JWT in Swagger and add `X-Organization-Id` via your
client or browser devtools when testing multi-org.

## Related

- [login.md](login.md) — obtain access token
- [logout.md](logout.md) — invalidate session
- [refresh.md](refresh.md) — renew access token
- [README.md](README.md) — auth route index
- [../users/list-organizations.md](../users/list-organizations.md) — list org memberships
- Code: `backend/src/presentation/dependencies/organization_context.py`,
  `backend/src/application/auth/services/authenticate_bearer.py`
