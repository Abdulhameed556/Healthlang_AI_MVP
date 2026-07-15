# POST /admin/api/v1/organizations/invitations

## URL

**Path:** `/admin/api/v1/organizations/invitations`

**Full URL (local):** `http://localhost:8000/admin/api/v1/organizations/invitations`

**See also:** [organizations README](README.md) · [login.md](../auth/login.md)

## Summary

**Admin-only.** Provisions a new product **organization** and its **super-admin
user** (status `INVITED`), then returns the invitation link the invitee uses to
set their password and activate. The admin calls the backend over the internal
API key under the hood — the frontend just calls this one endpoint.

Requires the **`admin`** role; `read_only` admins are rejected with 403.

## Auth

```http
Authorization: Bearer <access_token>
```

## Request

```json
{
  "email": "john.doe@acme.com",
  "organization_name": "Acme Corp",
  "industry": "Technology",
  "first_name": "John",
  "last_name": "Doe",
  "description": "AI-powered customer support platform",
  "organization_size": "50-200"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `email` | yes | Super-admin (invitee) email |
| `organization_name` | yes | 1–255 chars |
| `industry` | yes | 1–100 chars |
| `first_name` | yes | 1–100 chars |
| `last_name` | yes | 1–100 chars |
| `description` | no | Up to 5000 chars |
| `organization_size` | no | Up to 50 chars (e.g. `50-200`) |

## Response (201)

Returned directly (admin success responses are not enveloped):

```json
{
  "status": "success",
  "email": "john.doe@acme.com",
  "invitation_link": "https://supportos-dev.getindex.ai/invite?org=Acme+Corp&user_email=john.doe%40acme.com&su_o=true&token=xzx2gtB4Vn0f8c36"
}
```

The invite URL structure is:
```
{PRODUCT_APP_BASE_URL}/invite?org=<org_name>&user_email=<email>&su_o=true&token=<token>
```

| Environment | Base URL |
|-------------|----------|
| Dev | `https://supportos-dev.getindex.ai` |
| Prod | `https://supportos.getindex.ai` |

| Field | Description |
|-------|-------------|
| `status` | Always `success` on 201 |
| `email` | The invited email |
| `invitation_link` | Link the invitee opens to set a password and activate |

## Errors

| Status | When |
|--------|------|
| 401 | Missing/invalid admin Bearer token |
| 403 | Caller is `read_only` (not an admin) |
| 409 | A user with this email already exists |
| 422 | Validation error (missing/invalid fields) |

## Frontend notes

- This is the admin "invite an organization" form: collect the org + invitee
  details and POST them here.
- Show the returned `invitation_link` (or confirm the email was sent). The invitee
  activates via the product app's accept-invitation flow.

## Code

- Endpoint: `admin/src/presentation/api/v1/organizations/endpoints/invitations.py`
- Use-case: `admin/src/application/organizations/use_cases/invite_product_user.py`
