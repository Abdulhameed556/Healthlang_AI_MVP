# POST /api/v1/api-tools/test

## URL

**Path:** `/api/v1/api-tools/test`

**Full URL:** `<base>/api/v1/api-tools/test`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/api-tools/test` |

**See also:** [api_tools README](README.md) · [test-api-tool.md](test-api-tool.md) · [create-api-tool.md](create-api-tool.md)

## Summary

Validates and executes a GET request for an **unsaved** API tool configuration. Use this from
the create/edit form ("Test connection") before persisting. The server does not read from the
database — the full config is sent in the request body.

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

Tool configuration (same as create) **plus** sample values in `parameters`:

```json
{
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
  ],
  "parameters": {
    "user_id": 1
  },
  "auth_key": "optional-bearer-token"
}
```

### Fields

| Field | Required | Notes |
|-------|----------|-------|
| `endpoint_url` | yes | May include `{name}` placeholders for path params |
| `headers` | no | Applied as-is; use `is_secret: true` for sensitive header values |
| `request_parameters` | no | Schema used for validation |
| `parameters` | no | Sample values keyed by parameter name |
| `auth_key` | no | Sent as `Authorization: Bearer …` for this test only |

### Parameter value types

Values in `parameters` must match `request_parameters[].type`:

| `type` | Example value |
|--------|----------------|
| `string` | `"abc"` |
| `integer` | `1` (not `"1"`) |
| `number` | `1` or `1.5` |
| `boolean` | `true` or `false` |

Path param `user_id` with type `integer` → `"parameters": { "user_id": 1 }`.

## Success (200)

The SupportOs API returns **200** when the test call completes. Check `data.http_status` for
the upstream HTTP status (e.g. 404 from the external API).

```json
{
  "message": "API tool test completed",
  "status_code": 200,
  "error": false,
  "data": {
    "request_url": "https://jsonplaceholder.typicode.com/users/1",
    "http_status": 200,
    "response_body": {
      "id": 1,
      "name": "Leanne Graham",
      "email": "Sincere@april.biz"
    },
    "response_headers": {
      "content-type": "application/json; charset=utf-8"
    },
    "duration_ms": 142
  }
}
```

### `data` fields

| Field | Description |
|-------|-------------|
| `request_url` | Final URL after path substitution and query string |
| `http_status` | Upstream HTTP status code |
| `response_body` | Parsed JSON or raw text from upstream |
| `response_headers` | Upstream response headers |
| `duration_ms` | Round-trip time in milliseconds |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 422 | Unknown/missing/invalid parameters; path/query config mismatch |
| 502 | Upstream timeout, network failure, or response too large |

## Frontend notes

- Use on create/edit forms before save.
- For testing a **saved** tool, use [test-api-tool.md](test-api-tool.md) instead (smaller body).
- Do not log `auth_key` in the browser console or analytics.

## Code

- Endpoint: `src/presentation/api/v1/api_tools/endpoints/test_draft.py`
- Use-case: `src/application/api_tools/use_cases/test_api_tool_draft.py`
