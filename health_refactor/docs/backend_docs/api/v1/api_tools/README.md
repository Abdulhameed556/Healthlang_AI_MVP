# API Tools API (`/api/v1/api-tools`)

JWT-protected, organization-scoped HTTP GET tools for agents. Tools are linked to agents via
`api_tool_ids` on [agent create/update](../agents/create-agent.md) — there are no separate
attach/detach routes in v1.

Send `Authorization: Bearer <access_token>` on every call. Obtain the token from
[login](../auth/login.md) or [Google login](../auth/google-login.md). For multi-org
users, optionally add `X-Organization-Id` — see
[organization context](../auth/organization-context.md).

| Doc | Method | Path | Who can call |
|-----|--------|------|--------------|
| [list-api-tools.md](list-api-tools.md) | GET | `/api/v1/api-tools/` | All roles |
| [create-api-tool.md](create-api-tool.md) | POST | `/api/v1/api-tools/` | `super_admin`, `admin` |
| [get-api-tool.md](get-api-tool.md) | GET | `/api/v1/api-tools/{api_tool_id}` | All roles |
| [update-api-tool.md](update-api-tool.md) | PUT | `/api/v1/api-tools/{api_tool_id}` | `super_admin`, `admin` |
| [delete-api-tool.md](delete-api-tool.md) | DELETE | `/api/v1/api-tools/{api_tool_id}` | `super_admin`, `admin` |
| [test-api-tool-draft.md](test-api-tool-draft.md) | POST | `/api/v1/api-tools/test` | `super_admin`, `admin` |
| [test-api-tool.md](test-api-tool.md) | POST | `/api/v1/api-tools/{api_tool_id}/test` | `super_admin`, `admin` |

## Response envelope

All endpoints return:

```json
{
  "message": "…",
  "status_code": 200,
  "error": false,
  "data": { }
}
```

On failure, `error` is `true` and `data` is typically `null`.

## Categorical fields

### `http_method`

| Value | Supported |
|-------|-----------|
| `GET` | yes (v1 only) |

`POST`, `PUT`, and `PATCH` are not supported in v1.

### `request_parameters[].type`

| Value | JSON type in test `parameters` |
|-------|--------------------------------|
| `string` | string |
| `integer` | integer (not boolean) |
| `number` | integer or float |
| `boolean` | boolean |

### `request_parameters[].location`

| Value | Description |
|-------|-------------|
| `query` | Sent as `?name=value` (default) |
| `path` | Substituted into `endpoint_url` as `{name}` |

Path rules:

- Every `{param}` in `endpoint_url` must have a matching parameter with `location: "path"`.
- Every path parameter must appear as `{name}` in `endpoint_url`.
- Query parameters cannot reuse placeholder names from the URL.

Example URL: `https://api.example.com/users/{user_id}` with path param `user_id` and optional
query param `include_orders`.

## Shared tool shape

Create, update, and get return the same `data` object (see [get-api-tool.md](get-api-tool.md)).

### Top-level fields

| Field | Create | Update | Get | Notes |
|-------|--------|--------|-----|-------|
| `name` | required | required | yes | `snake_case`; unique per org; exposed to LLM |
| `description` | required | required | yes | 1–5000 chars; shown to LLM |
| `endpoint_url` | required | required | yes | GET target; use `{name}` for path params |
| `http_method` | optional | — | yes | Default `GET`; only `GET` in v1 |
| `headers` | optional | optional | yes | List of `{ key, value, is_secret? }`; default `[]` |
| `request_parameters` | optional | optional | yes | Typed parameter schema; default `[]` |
| `auth_key` | optional | optional | yes | Plain text in; encrypted at rest; **returned decrypted** on get/list/create/update |
| `api_tool_id` | — | — | yes | Server-assigned UUID |
| `created_at` / `updated_at` | — | — | yes | ISO 8601 datetimes |

### `headers[]`

| Field | Required | Limits | Notes |
|-------|----------|--------|-------|
| `key` | yes | 1–255 chars | HTTP header name |
| `value` | yes | 1–2000 chars | Plain on write; decrypted on read |
| `is_secret` | no | boolean | Default `false`. When `true`, value is encrypted at rest (e.g. `X-Api-Key`) |

Duplicate header keys → 422.

Non-secret headers (e.g. `Accept: application/json`) can leave `is_secret` false. Use
`is_secret: true` for API keys and other sensitive header values.

### `request_parameters[]`

| Field | Required | Notes |
|-------|----------|-------|
| `name` | yes | `snake_case`; max 100 chars |
| `type` | yes | `string` \| `integer` \| `number` \| `boolean` |
| `location` | no | `query` (default) \| `path` |
| `required` | no | Default `false` |
| `description` | no | Max 500 chars; helps LLM fill args |
| `default` | no | Must match `type` when set |

Duplicate parameter names → 422.

### `auth_key` behavior

Secrets are encrypted in the database using `API_TOOL_SECRETS_ENCRYPTION_KEY` (server env).
Authenticated org members who can read tools receive **decrypted** values on get/list.

| Action | Behavior |
|--------|----------|
| Create with `auth_key` | Encrypted and stored |
| Update with `auth_key` | Replaces stored encrypted value |
| Update omitting `auth_key` | Keeps existing encrypted value |
| Get / list / create / update response | Returns decrypted `auth_key`, or `null` if unset |
| Test saved tool | Uses stored auth automatically; optional `auth_key` in body overrides for one test |
| Test draft | Pass plain `auth_key` in body (not persisted) |

### Secret header update behavior

On update, for a header with `is_secret: true`:

- Send the plain value from get (re-encrypts on save), **or**
- Send `"********"` as `value` to keep the existing encrypted value unchanged

### Full tool example (`data` on create / get / update)

```json
{
  "api_tool_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "get_user",
  "description": "Fetch a user from the JSONPlaceholder public API.",
  "http_method": "GET",
  "endpoint_url": "https://jsonplaceholder.typicode.com/users/{user_id}",
  "headers": [
    { "key": "Accept", "value": "application/json", "is_secret": false },
    { "key": "X-Api-Key", "value": "sk-live-example", "is_secret": true }
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
  "updated_at": "2026-06-04T12:00:00Z"
}
```

## Typical UI flow

1. **List** tools → [list-api-tools.md](list-api-tools.md)
2. **Test draft** from create/edit form → [test-api-tool-draft.md](test-api-tool-draft.md)
3. **Create** or **update** → [create-api-tool.md](create-api-tool.md) / [update-api-tool.md](update-api-tool.md)
4. **Test saved** tool → [test-api-tool.md](test-api-tool.md)
5. **Link** to agent via `api_tool_ids` on agent create/update
6. **Delete** when unused → [delete-api-tool.md](delete-api-tool.md) (409 if still attached to an agent)

**Related:** [../agents/README.md](../agents/README.md) · [../auth/login.md](../auth/login.md)
