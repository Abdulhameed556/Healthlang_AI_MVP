# API Tools — endpoint plan (v1)

Org-scoped HTTP tools for agents. Linked to agents via `api_tool_ids` on agent create/update (no separate attach API in v1).

## Routes

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/v1/api-tools/` | JWT (all roles) | Paginated list |
| `POST` | `/api/v1/api-tools/` | `super_admin` / `admin` | Create tool |
| `GET` | `/api/v1/api-tools/{api_tool_id}` | JWT (all roles) | Get by id |
| `PUT` | `/api/v1/api-tools/{api_tool_id}` | `super_admin` / `admin` | Full update |
| `DELETE` | `/api/v1/api-tools/{api_tool_id}` | `super_admin` / `admin` | Delete (409 if attached) |

## Payload

| Field | Create | Update | Notes |
|-------|--------|--------|-------|
| `name` | required | required | `snake_case`, unique per org |
| `description` | required | required | Shown to LLM as tool description |
| `endpoint_url` | required | required | GET target; use `{param}` for path params |
| `http_method` | optional | — | `GET` only (immutable default) |
| `headers` | optional | optional | List of `{ "key", "value" }`; default `[]` |
| `request_parameters` | optional | optional | Typed list (see below) |
| `auth_key` | optional | optional | Plain text in; stored hashed; never returned |

### `request_parameters[]` (enforced, not free JSON)

| Field | Required | Values |
|-------|----------|--------|
| `name` | yes | `snake_case` param name |
| `type` | yes | `string` \| `integer` \| `number` \| `boolean` |
| `location` | no | `query` (default) \| `path` — path params must match `{name}` in `endpoint_url` |
| `required` | no | default `false` |
| `description` | no | Helps LLM fill args |
| `default` | no | Must match `type` when set |

Duplicate param names → 422.

## LangChain mapping (AI service, later)

- `name` → tool name
- `description` → tool description
- `request_parameters` → dynamic Pydantic `args_schema`
- `endpoint_url` / `headers` / auth → executor only

## Out of scope (v1)

- `POST/PUT/PATCH` HTTP methods
- Attach/detach endpoints (use agent `api_tool_ids`)
- Embedding full tools in deploy snapshot (follow-up)
