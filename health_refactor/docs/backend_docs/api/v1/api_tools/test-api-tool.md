# POST /api/v1/api-tools/{api_tool_id}/test

## URL

**Path:** `/api/v1/api-tools/{api_tool_id}/test`

**Full URL:** `<base>/api/v1/api-tools/{api_tool_id}/test`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/api-tools/550e8400-e29b-41d4-a716-446655440000/test` |

**See also:** [api_tools README](README.md) · [test-api-tool-draft.md](test-api-tool-draft.md) · [get-api-tool.md](get-api-tool.md)

## Summary

Tests a **saved** API tool. Loads configuration from the database (URL, headers, parameter
schema), validates sample values, executes a GET, and returns the upstream response.

Use [test-api-tool-draft.md](test-api-tool-draft.md) for unsaved configs on the create/edit form.

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
| `api_tool_id` | UUID | Saved tool to test |

## Request body

`Content-Type: application/json`

Only sample values — config comes from the stored tool:

```json
{
  "parameters": {
    "user_id": 1
  },
  "auth_key": "optional-bearer-token"
}
```

### Fields

| Field | Required | Notes |
|-------|----------|-------|
| `parameters` | no | Sample values keyed by parameter name; default `{}` |
| `auth_key` | no | Optional override for this test only; stored auth is used automatically when omitted |

Stored `headers` from the tool are always applied. Clients cannot override headers on test in v1.

### Parameter value types

Same rules as [test-api-tool-draft.md](test-api-tool-draft.md#parameter-value-types).

## Success (200)

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
      "name": "Leanne Graham"
    },
    "response_headers": {
      "content-type": "application/json; charset=utf-8"
    },
    "duration_ms": 120
  }
}
```

Response `data` shape matches [test-api-tool-draft.md](test-api-tool-draft.md#success-200).

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Tool not found or not in caller's organization |
| 422 | Unknown/missing/invalid parameters |
| 502 | Upstream timeout, network failure, or response too large |

## Frontend notes

- Use on the tool detail page after save.
- Stored bearer auth and secret headers are applied automatically; pass `auth_key` only to test a different token without saving.
- Upstream 4xx/5xx still returns SupportOs **200** — surface `data.http_status` in the UI.

## Code

- Endpoint: `src/presentation/api/v1/api_tools/endpoints/test.py`
- Use-case: `src/application/api_tools/use_cases/test_api_tool.py`
