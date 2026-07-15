# GET /api/v1/api-tools/{api_tool_id}

## URL

**Path:** `/api/v1/api-tools/{api_tool_id}`

**Full URL:** `<base>/api/v1/api-tools/{api_tool_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/api-tools/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [api_tools README](README.md) · [list-api-tools.md](list-api-tools.md) · [update-api-tool.md](update-api-tool.md)

## Summary

Returns the full API tool configuration for the caller's organization.

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
| `api_tool_id` | UUID | Tool to load |

## Success (200)

```json
{
  "message": "API tool retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "api_tool_id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "get_user",
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
    "auth_key": "optional-bearer-token",
    "created_at": "2026-06-04T12:00:00Z",
    "updated_at": "2026-06-04T12:00:00Z"
  }
}
```

`auth_key` is `null` when not configured; otherwise returned decrypted for editing. Field
reference: [README — shared tool shape](README.md#shared-tool-shape).

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 404 | Tool not found or not in caller's organization |
| 422 | Invalid `api_tool_id` format |

## Frontend notes

- Use this payload to populate the edit form, including `auth_key` and secret header values.
- On update, omit `auth_key` to keep the existing token; send a new value to replace.

## Code

- Endpoint: `src/presentation/api/v1/api_tools/endpoints/detail.py`
- Use-case: `src/application/api_tools/use_cases/get_api_tool.py`
