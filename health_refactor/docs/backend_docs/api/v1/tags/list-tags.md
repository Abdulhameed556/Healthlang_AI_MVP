# GET /api/v1/tags/

## URL

**Path:** `/api/v1/tags/`

**Full URL:** `<base>/api/v1/tags/`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/tags/` |

**See also:** [tags README](README.md) · [create-tag.md](create-tag.md) · [get-tag.md](get-tag.md)

## Summary

Returns a paginated list of the organization's classification tags, with optional
free-text search over tag value and description.

## Auth

```http
Authorization: Bearer <access_token>
```

Optional `X-Organization-Id: <uuid>` for multi-org users — [organization-context.md](../auth/organization-context.md).

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Query parameters

All parameters are optional.

| Param | Type | Default | Limits | Description |
|-------|------|---------|--------|-------------|
| `search` | string | — | max 255 chars | Case-insensitive match over tag `value` and `description` |
| `page` | integer | `1` | ≥ 1 | Page number (1-based) |
| `page_size` | integer | `20` | 1–100 | Tags per page |

**Example:** `GET /api/v1/tags/?search=refund&page=1&page_size=20`

## Success (200)

```json
{
  "message": "Tags retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "tags": [
      {
        "tag_id": "550e8400-e29b-41d4-a716-446655440000",
        "value": "refund_request",
        "description": "Customer is asking for their money back.",
        "created_at": "2026-06-20T12:00:00Z",
        "updated_at": "2026-06-20T12:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### `data.tags[]` fields

See [README — tag shape](README.md#tag-shape).

### Pagination fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total tags matching the search |
| `page` | integer | Current page |
| `page_size` | integer | Page size used |
| `total_pages` | integer | `0` when `total` is `0` |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 422 | Invalid query parameter (e.g. `page=0`, `page_size>100`) |

## Frontend notes

- Default to `page=1` and `page_size=20`; expose page size up to 100.
- Use `total_pages` for pagination UI.
- The same endpoint powers both the catalog table and the search box.

## Code

- Endpoint: `src/presentation/api/v1/tags/endpoints/list.py`
- Schemas: `src/presentation/api/v1/tags/schemas.py`
- Use-case: `src/application/tags/use_cases/list_tags.py`
