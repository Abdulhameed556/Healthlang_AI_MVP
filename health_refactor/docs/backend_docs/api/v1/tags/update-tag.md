# PUT /api/v1/tags/{tag_id}

## URL

**Path:** `/api/v1/tags/{tag_id}`

**Full URL:** `<base>/api/v1/tags/{tag_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/tags/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [tags README](README.md) · [list-tags.md](list-tags.md) · [delete-tag.md](delete-tag.md)

## Summary

Replaces a tag's `value` and `description`. This is a full replacement — both
fields are taken from the request body (`description` defaults to `""` if omitted).

Renaming a tag changes the label the AI assigns going forward; tickets already
labelled with the previous value keep that value.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | no (403) |

## Path parameters

| Param | Type | Description |
|-------|------|-------------|
| `tag_id` | UUID | Tag identifier |

## Request body

`Content-Type: application/json`

```json
{
  "value": "refund_requested",
  "description": "Customer explicitly requested a refund."
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `value` | yes | `snake_case`; unique per org; 1–64 chars; pattern `^[a-z0-9]+(_[a-z0-9]+)*$` |
| `description` | no | Default `""`; max 500 chars |

Field reference: [README — tag shape](README.md#tag-shape).

## Success (200)

```json
{
  "message": "Tag updated successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "tag_id": "550e8400-e29b-41d4-a716-446655440000",
    "value": "refund_requested",
    "description": "Customer explicitly requested a refund.",
    "created_at": "2026-06-20T12:00:00Z",
    "updated_at": "2026-06-20T13:30:00Z"
  }
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Tag not found in the caller's organization |
| 409 | New `value` collides with another tag in the organization |
| 422 | Validation failure (e.g. non-snake_case `value`, malformed `tag_id`) |

## Code

- Endpoint: `src/presentation/api/v1/tags/endpoints/update.py`
- Schemas: `src/presentation/api/v1/tags/schemas.py`
- Use-case: `src/application/tags/use_cases/update_tag.py`
