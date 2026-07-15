# POST /api/v1/api-tools/

## URL

**Path:** `/api/v1/api-tools/`

**Full URL:** `<base>/api/v1/api-tools/`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/api-tools/` |

**See also:** [api_tools README](README.md) · [test-api-tool-draft.md](test-api-tool-draft.md) · [update-api-tool.md](update-api-tool.md)

## Summary

Creates an org-scoped HTTP GET tool for agent use. The tool name is exposed to the LLM as the
function name.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|----------|
| `super_admin` | yes |
| `admin` | yes |
| `read_only` | no (403) |

## Request body

`Content-Type: application/json`

```json
{
  "name": "get_user",
  "description": "Fetch a user from the JSONPlaceholder public API.",
  "endpoint_url": "https://jsonplaceholder.typicode.com/users/{user_id}",
  "http_method": "GET",
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
  ],
  "auth_key": "optional-bearer-token"
}
```

### Top-level fields

| Field | Required | Notes |
|-------|----------|-------|
| `name` | yes | `snake_case`; unique per org; 1–255 chars |
| `description` | yes | 1–5000 chars |
| `endpoint_url` | yes | 1–2000 chars; use `{name}` for path params |
| `http_method` | no | Default `GET`; only `GET` supported in v1 |
| `headers` | no | Default `[]`; use `is_secret: true` for sensitive values |
| `request_parameters` | no | Default `[]` |
| `auth_key` | no | Plain text; encrypted at rest; returned decrypted on get/list/create/update |

Field reference: [README — shared tool shape](README.md#shared-tool-shape).

### Path + query example

```json
{
  "name": "get_customer_context",
  "description": "Fetch customer with optional order history.",
  "endpoint_url": "https://internal.example.com/customers/{customer_id}",
  "request_parameters": [
    {
      "name": "customer_id",
      "type": "string",
      "location": "path",
      "required": true,
      "description": "Customer UUID"
    },
    {
      "name": "include_orders",
      "type": "boolean",
      "location": "query",
      "required": false,
      "description": "Include recent orders"
    }
  ]
}
```

## Success (201)

```json
{
  "message": "API tool created successfully",
  "status_code": 201,
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
}
```

Response `data` matches [get-api-tool.md](get-api-tool.md). Server assigns `api_tool_id` and
timestamps. If `auth_key` was sent on create, the response includes the decrypted value (same as get).

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 409 | Duplicate tool name in organization |
| 422 | Validation failure (invalid name, path/query mismatch, duplicate headers/params, type mismatch on `default`, etc.) |

## Frontend notes

- Use [test-api-tool-draft.md](test-api-tool-draft.md) to validate config before create.
- After create, store `data.api_tool_id` for edit, test, and agent linking.
- Avoid logging `auth_key` or secret header values in browser analytics.

## Code

- Endpoint: `src/presentation/api/v1/api_tools/endpoints/create.py`
- Schemas: `src/presentation/api/v1/api_tools/schemas.py`
- Use-case: `src/application/api_tools/use_cases/create_api_tool.py`
