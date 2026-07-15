# GET /api/v1/tags/{tag_id}

## URL

**Path:** `/api/v1/tags/{tag_id}`

**Full URL:** `<base>/api/v1/tags/{tag_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/tags/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [tags README](README.md) · [list-tags.md](list-tags.md) · [update-tag.md](update-tag.md)

## Summary

Returns a single tag by id, scoped to the caller's organization.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Path parameters

| Param | Type | Description |
|-------|------|-------------|
| `tag_id` | UUID | Tag identifier |

## Success (200)

```json
{
  "message": "Tag retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "tag_id": "550e8400-e29b-41d4-a716-446655440000",
    "value": "refund_request",
    "description": "Customer is asking for their money back.",
    "created_at": "2026-06-20T12:00:00Z",
    "updated_at": "2026-06-20T12:00:00Z"
  }
}
```

Field reference: [README — tag shape](README.md#tag-shape).

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 404 | Tag not found in the caller's organization |
| 422 | Malformed `tag_id` (not a UUID) |

## Code

- Endpoint: `src/presentation/api/v1/tags/endpoints/detail.py`
- Schemas: `src/presentation/api/v1/tags/schemas.py`
- Use-case: `src/application/tags/use_cases/get_tag.py`
