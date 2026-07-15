# GET /api/v1/agents/

## URL

**Path:** `/api/v1/agents/`

**Full URL:** `<base>/api/v1/agents/`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/` |

**See also:** [agents README](README.md) · [create-agent.md](create-agent.md) · [get-agent.md](get-agent.md)

## Summary

Returns a paginated list of agent summaries for the caller's organization. Use this for the agents table / picker; call [get-agent.md](get-agent.md) for the full configuration.

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

All parameters are optional. Filters combine with **AND**.

| Param | Type | Default | Limits | Description |
|-------|------|---------|--------|-------------|
| `search` | string | — | max 255 chars | Case-insensitive match on the agent `name` |
| `agent_type` | string | — | `chat` \| `voice` | Filter by agent type |
| `status` | string | — | `inactive` \| `deployed` | Filter by agent status |
| `page` | integer | `1` | ≥ 1 | Page number (1-based) |
| `page_size` | integer | `20` | 1–100 | Agents per page |

Notes:

- `search` is case-insensitive and matches partial values.
- `agent_type` and `status` accept a single value each; unknown values → `422`.

**Example:** `GET /api/v1/agents/?search=support&agent_type=chat&status=deployed&page=1&page_size=20`

## Success (200)

```json
{
  "message": "Agents retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "agents": [
      {
        "agent_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Support Bot",
        "type": "chat",
        "status": "inactive",
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

### `data.agents[]` fields

| Field | Type | Notes |
|-------|------|-------|
| `agent_id` | UUID | Agent identifier |
| `name` | string | Display name |
| `type` | string | `chat` \| `voice` |
| `status` | string | `inactive` \| `deployed` |
| `created_at` | ISO 8601 datetime | |
| `updated_at` | ISO 8601 datetime | |

### Pagination fields

| Field | Type | Description |
|-------|------|-------------|
| `total` | integer | Total agents in the organization |
| `page` | integer | Current page |
| `page_size` | integer | Page size used |
| `total_pages` | integer | `0` when `total` is `0` |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 422 | Invalid query parameter (e.g. `page=0`, unknown `agent_type` or `status`) |

## Frontend notes

- Default to `page=1` and `page_size=20`; expose page size up to 100.
- Use `total_pages` for pagination UI; do not assume a fixed page count.
- The same endpoint powers the table and the search box — send `search` for free-text
  and/or the `agent_type` / `status` filters; they combine.
- Summary rows omit rules, scenarios, and attachments — load [get-agent.md](get-agent.md) for the editor.

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/list.py`
- Use-case: `src/application/agents/use_cases/list_agents.py`
