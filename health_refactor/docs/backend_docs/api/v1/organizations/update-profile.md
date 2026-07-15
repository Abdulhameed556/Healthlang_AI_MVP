# PATCH /api/v1/organizations/me

## URL

**Path:** `/api/v1/organizations/me`

**Full URL:** `<base>/api/v1/organizations/me`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/organizations/me` |

## Summary

Updates the **organization profile** for the tenant tied to the current JWT session.
Editable fields: `name`, `industry`, `description`.

Requires `super_admin` or `admin`. `read_only` receives **403**.

Read profile first: [me.md](me.md).

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | no (403) |

## Request

- Content-Type: `application/json`
- At least **one** field required

```json
{
  "name": "Acme Corp",
  "industry": "healthcare",
  "description": "Updated blurb"
}
```

| Field | Required | Notes |
|-------|----------|--------|
| `name` | no* | Organization display name |
| `industry` | no* | Industry label |
| `description` | no* | Send `""` to clear |

\*At least one of the three must be present.

`size` and `status` cannot be changed from this API.

## Response (200)

```json
{
  "message": "Organization profile updated successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "organization_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Acme Corp",
    "industry": "healthcare",
    "description": "Updated blurb",
    "size": "11-50",
    "status": "active"
  }
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Organization not found |
| 422 | No fields in body or validation failed |

## Code

- Endpoint: `admin/src/presentation/api/v1/organizations/endpoints/me.py`
- Use-case: `admin/src/application/organizations/use_cases/update_organization_profile.py`
