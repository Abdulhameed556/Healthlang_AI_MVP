# GET /api/v1/agents/{agent_id}/versions

## URL

**Path:** `/api/v1/agents/{agent_id}/versions`

**Full URL:** `<base>/api/v1/agents/{agent_id}/versions`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000/versions?page=1&page_size=20` |

**See also:** [agents README](README.md) · [publish-agent.md](publish-agent.md) · [deploy-version.md](deploy-version.md) · [get-version.md](get-version.md)

## Summary

Returns a **paginated history** of published version snapshots for an agent, **newest first**. Each row carries:

- `is_deployed` — `true` for the currently **live** version (not necessarily the newest, e.g. after a rollback).
- `created_by` — who published it.
- `changes_applied` — backend-computed human-readable diff vs the previous version.
- `change_note` — optional free-text note from publish.

The editable **draft** is **not** part of this list — fetch it separately from [get-agent.md](get-agent.md) and render it as a pinned row in the UI.

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
| `agent_id` | UUID | Agent whose versions to list |

## Query parameters

| Param | Type | Default | Limits |
|-------|------|---------|--------|
| `page` | integer | 1 | ≥ 1 |
| `page_size` | integer | 20 | 1–100 |

## Success (200)

```json
{
  "message": "Agent versions retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "items": [
      {
        "version_id": "550e8400-e29b-41d4-a716-446655440011",
        "agent_id": "550e8400-e29b-41d4-a716-446655440000",
        "version_number": 2,
        "configuration_snapshot": { },
        "created_at": "2026-06-04T14:00:00Z",
        "created_by": "550e8400-e29b-41d4-a716-446655440050",
        "changes_applied": ["Rule 'Privacy' updated"],
        "change_note": null,
        "is_deployed": true
      },
      {
        "version_id": "550e8400-e29b-41d4-a716-446655440010",
        "agent_id": "550e8400-e29b-41d4-a716-446655440000",
        "version_number": 1,
        "configuration_snapshot": { },
        "created_at": "2026-06-04T13:00:00Z",
        "created_by": "550e8400-e29b-41d4-a716-446655440050",
        "changes_applied": ["Initial version published"],
        "change_note": null,
        "is_deployed": false
      }
    ],
    "total": 2,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### `data` fields

| Field | Type | Description |
|-------|------|-------------|
| `items[]` | array | Version rows, newest first |
| `items[].version_id` | UUID | Version record id |
| `items[].version_number` | integer | Publish sequence number |
| `items[].configuration_snapshot` | object | Immutable config; see [get-agent.md](get-agent.md) shape |
| `items[].created_at` | ISO 8601 datetime | Publish timestamp |
| `items[].created_by` | UUID \| null | User who published |
| `items[].changes_applied` | string[] | Human-readable diff vs previous version |
| `items[].change_note` | string \| null | Optional note from publish |
| `items[].is_deployed` | boolean | `true` for the currently live version |
| `total` | integer | Total versions for the agent |
| `page` / `page_size` / `total_pages` | integer | Pagination metadata |

Empty `items` array when the agent has never been published.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 404 | Agent not found or not in caller's organization |
| 422 | Invalid `agent_id`, or `page`/`page_size` out of range |

## Frontend notes

- **Live badge:** use the `is_deployed` flag directly — no need to cross-reference deploy responses.
- **Draft row:** render the editable draft from [get-agent.md](get-agent.md) as a separate pinned card; it is not in `items`.
- **Restore:** load a row's full snapshot via [get-version.md](get-version.md), then save into the draft with [update-agent.md](update-agent.md).
- **Go live / rollback:** [deploy-version.md](deploy-version.md) with the row's `version_id`.

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/versions.py`
- Use-case: `src/application/agents/use_cases/list_agent_versions.py`
