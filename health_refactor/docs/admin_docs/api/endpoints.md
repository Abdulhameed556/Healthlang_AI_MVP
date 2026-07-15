# Admin Panel API — Endpoint Reference

All routes prefixed `/admin/api/v1`. Auth = Admin Panel JWT (separate from
backend JWT). Role column shows minimum required role. Rows marked *(planned)*
are not yet wired.

## Auth

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| POST | /auth/login/initiate | — | — | Step 1: email/password → sends OTP |
| POST | /auth/login/verify | — | — | Step 2: email/OTP → issues access token |
| POST | /auth/logout | JWT | Any | Invalidate session |
| POST | /auth/invitations/{token}/accept | — | — | *(planned)* Accept invite, set password |
| POST | /auth/password/change | JWT | Any | *(planned)* Change password |

## Admin Panel Users

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | /users/me | JWT | `admin`, `read_only` | Current admin's own profile → [v1/users/me.md](v1/users/me.md) |
| GET | /users | JWT | Any | *(planned)* List admin panel users |
| POST | /users/invite | JWT | Admin | *(planned)* Invite a new admin panel user |
| GET | /users/{id} | JWT | Any | *(planned)* Get user detail |
| PATCH | /users/{id}/role | JWT | Admin | *(planned)* Change role |
| DELETE | /users/{id} | JWT | Admin | *(planned)* Remove user |
| POST | /users/{id}/unlock | JWT | Admin | *(planned)* Unlock locked account |
| POST | /users/{id}/invite/resend | JWT | Admin | *(planned)* Resend invite (Pending only) |

## Organizations

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| POST | /organizations/invitations | JWT | Admin | Provision org + super-admin (INVITED) → [v1/organizations/invitations.md](v1/organizations/invitations.md) |
| GET | /organizations | JWT | Admin | List all orgs with activation status → [v1/organizations/list.md](v1/organizations/list.md) |
| GET | /organizations/{id} | JWT | Admin | Org details, agent count, users → [v1/organizations/detail.md](v1/organizations/detail.md) |
| POST | /organizations/onboard | JWT | Admin | *(planned)* Onboard new organization |
| GET | /organizations/{id}/users | JWT | Any | *(planned)* Org users list |
| GET | /organizations/{id}/agents | JWT | Any | *(planned)* Org agents list |
| POST | /organizations/{id}/disable | JWT | Admin | *(planned)* Disable organization |
| POST | /organizations/{id}/enable | JWT | Admin | *(planned)* Enable organization |

## Dashboard

| Method | Path | Auth | Role | Description |
|---|---|---|---|---|
| GET | /dashboard/metrics | JWT | Any | *(planned)* Platform-wide metrics snapshot |
