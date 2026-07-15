# PUT /api/v1/api-tools/{api_tool_id}

## URL

**Path:** `/api/v1/api-tools/{api_tool_id}`

**Full URL:** `<base>/api/v1/api-tools/{api_tool_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/api-tools/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [api_tools README](README.md) · [get-api-tool.md](get-api-tool.md) · [test-api-tool-draft.md](test-api-tool-draft.md)

## Summary

Replaces an API tool configuration. This is a **full replace** of all mutable fields (same
semantics as agent update).

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
| `api_tool_id` | UUID | Tool to update |

## Request body

`Content-Type: application/json`

Same shape as [create-api-tool.md](create-api-tool.md), except:

| Field | Notes |
|-------|-------|
| `http_method` | Not accepted on update (immutable `GET`) |
| `auth_key` | Omit to keep existing encrypted value; send new value to replace; send `null` or `""` to clear |
| Secret `headers[]` | Send plain value from get to replace; send `"********"` with `is_secret: true` to keep unchanged |

```json
{
  "name": "get_user_v2",
  "description": "Fetch a user from the JSONPlaceholder public API.",
  "endpoint_url": "https://jsonplaceholder.typicode.com/users/{user_id}",
  "headers": [
    { "key": "Accept", "value": "application/json" }
  ],
  "request_parameters": [
    {
      "name": "user_id",
      "type": "integer",
      "location": "path",
      "required": true,
      "description": "User ID"
    }
  ]
}
```

## Success (200)

```json
{
  "message": "API tool updated successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "api_tool_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "get_user_v2",
    "description": "Fetch a user from the JSONPlaceholder public API.",
    "http_method": "GET",
    "endpoint_url": "https://jsonplaceholder.typicode.com/users/{user_id}",
    "headers": [
      { "key": "Accept", "value": "application/json", "is_secret": false }
    ],
    "auth_key": "optional-bearer-token",
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
    "updated_at": "2026-06-04T12:30:00Z"
  }
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Tool not found or not in caller's organization |
| 409 | Duplicate tool name in organization |
| 422 | Validation failure |

## Frontend notes

- Load current config from [get-api-tool.md](get-api-tool.md), let the user edit, then PUT the
  full body.
- Use [test-api-tool-draft.md](test-api-tool-draft.md) to test unsaved edits before save.

## Code

- Endpoint: `src/presentation/api/v1/api_tools/endpoints/update.py`
- Use-case: `src/application/api_tools/use_cases/update_api_tool.py`
