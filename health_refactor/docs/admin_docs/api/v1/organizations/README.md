# Organizations API (`/admin/api/v1/organizations`)

Admin-JWT-protected routes for managing product organizations.

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [invitations.md](invitations.md) | POST | `/admin/api/v1/organizations/invitations` | `admin` |
| [list.md](list.md) | GET | `/admin/api/v1/organizations` | `admin` |
| [detail.md](detail.md) | GET | `/admin/api/v1/organizations/{org_id}` | `admin` |

**Related**

- Login (get admin JWT): [../auth/login.md](../auth/login.md)
- Current admin profile: [../users/me.md](../users/me.md)
