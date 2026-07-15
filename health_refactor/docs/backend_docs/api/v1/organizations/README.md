# Organizations API (`/api/v1/organizations`)

JWT-protected tenant routes. Send `Authorization: Bearer <access_token>` on every call.

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [me.md](me.md) | GET | `/api/v1/organizations/me` | All roles |
| [update-profile.md](update-profile.md) | PATCH | `/api/v1/organizations/me` | `super_admin`, `admin` |
| [users.md](users.md) | GET | `/api/v1/organizations/users` | `super_admin`, `admin` |
| [remove-member.md](remove-member.md) | DELETE | `/api/v1/organizations/users/{user_id}` | `super_admin`, `admin` |
| [update-member-role.md](update-member-role.md) | PATCH | `/api/v1/organizations/users/{user_id}/role` | `super_admin`, `admin` |
| [invite-user.md](invite-user.md) | POST | `/api/v1/organizations/users/invite` | `super_admin`, `admin` |

**Related**

- Current user profile: [../users/me.md](../users/me.md)
- Login (get JWT): [../auth/login.md](../auth/login.md)
