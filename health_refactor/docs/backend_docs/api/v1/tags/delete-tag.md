# DELETE /api/v1/tags/{tag_id}

## URL

**Path:** `/api/v1/tags/{tag_id}`

**Full URL:** `<base>/api/v1/tags/{tag_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/tags/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [tags README](README.md) · [list-tags.md](list-tags.md) · [update-tag.md](update-tag.md)

## Summary

Deletes a tag from the organization's catalog. After deletion the AI will no longer
assign the tag and it stops being a valid [tickets list](../tickets/list-tickets.md)
filter value. Tickets already labelled with the tag keep their existing `tags`
(the value is not retroactively removed).

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

## Success (200)

```json
{
  "message": "Tag deleted successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "tag_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Tag not found in the caller's organization |
| 422 | Malformed `tag_id` (not a UUID) |

## Code

- Endpoint: `src/presentation/api/v1/tags/endpoints/delete.py`
- Schemas: `src/presentation/api/v1/tags/schemas.py`
- Use-case: `src/application/tags/use_cases/delete_tag.py`
