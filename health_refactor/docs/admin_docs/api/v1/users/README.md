# Users API (`/admin/api/v1/users`)

Admin-JWT-protected routes. Only the current-profile route is implemented today;
the staff-management routes (list/invite/remove/role/unlock) are planned.

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [me.md](me.md) | GET | `/admin/api/v1/users/me` | `admin`, `read_only` |

**Related**

- Login (get admin JWT): [../auth/login.md](../auth/login.md)
- Logout: [../auth/logout.md](../auth/logout.md)
