# GET /api/v1/api-tools/

## URL

**Path:** `/api/v1/api-tools/`

**Full URL:** `<base>/api/v1/api-tools/`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/api-tools/` |

**See also:** [api_tools README](README.md) · [create-api-tool.md](create-api-tool.md) · [get-api-tool.md](get-api-tool.md)

## Summary

Returns a paginated list of API tools for the caller's organization. Use this for the tools
table / picker; call [get-api-tool.md](get-api-tool.md) for the full configuration.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | yes |

## Query parameters

| Param | Type | Default | Limits | Description |
|-------|------|---------|--------|-------------|
| `page` | integer | `1` | ≥ 1 | Page number (1-based) |
| `page_size` | integer | `20` | 1–100 | Tools per page |

**Example:** `GET /api/v1/api-tools/?page=1&page_size=20`

## Success (200)

```json
{
  "message": "API tools retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "api_tools": [
      {
        "api_tool_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "get_user",
        "description": "Fetch a user from the JSONPlaceholder public API.",
        "http_method": "GET",
        "endpoint_url": "https://jsonplaceholder.typicode.com/users/{user_id}",
        "headers": [
          { "key": "Accept", "value": "application/json", "is_secret": false }
        ],
        "auth_key": null,
        "request_parameters": [
          {
            "name": "user_id",
            "type": "integer",
            "location": "path",
            "required": true,
            "description": "User ID",
            "default": null
          }
        ],
        "created_at": "2026-06-04T12:00:00Z",
        "updated_at": "2026-06-04T12:00:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### Pagination fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total tools in the organization |
| `page` | integer | Current page |
| `page_size` | integer | Page size used |
| `total_pages` | integer | `0` when `total` is `0` |

Each item in `api_tools[]` matches the full tool shape in [get-api-tool.md](get-api-tool.md),
including decrypted `auth_key` when configured.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 422 | Invalid query parameter (e.g. `page=0`) |

## Frontend notes

- Default to `page=1` and `page_size=20`; expose page size up to 100.
- Use `total_pages` for pagination UI.

## Code

- Endpoint: `src/presentation/api/v1/api_tools/endpoints/list.py`
- Use-case: `src/application/api_tools/use_cases/list_api_tools.py`
