# GET /api/v1/agents/{agent_id}/versions/{version_id}

## URL

**Path:** `/api/v1/agents/{agent_id}/versions/{version_id}`

**Full URL:** `<base>/api/v1/agents/{agent_id}/versions/{version_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000/versions/550e8400-e29b-41d4-a716-446655440010` |

**See also:** [agents README](README.md) · [list-versions.md](list-versions.md) · [deploy-version.md](deploy-version.md) · [get-agent.md](get-agent.md)

## Summary

Returns a single published version snapshot, including its author and human-readable change summary. Use this to **load a past version's content back into the editable draft** (fetch it, then save the snapshot fields via [update-agent.md](update-agent.md)).

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
| `agent_id` | UUID | Parent agent |
| `version_id` | UUID | Version to fetch |

## Success (200)

```json
{
  "message": "Agent version retrieved successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "version_id": "550e8400-e29b-41d4-a716-446655440010",
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "version_number": 2,
    "configuration_snapshot": { },
    "created_at": "2026-06-04T13:00:00Z",
    "created_by": "550e8400-e29b-41d4-a716-446655440050",
    "changes_applied": ["Brand voice prompt updated"],
    "change_note": "Tone tweak"
  }
}
```

### `data` fields

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | UUID | Version record id |
| `agent_id` | UUID | Parent agent |
| `version_number` | integer | Sequence number |
| `configuration_snapshot` | object | Immutable config; same nested shape as [get-agent.md](get-agent.md) |
| `created_at` | ISO 8601 datetime | Publish timestamp |
| `created_by` | UUID \| null | User who published |
| `changes_applied` | string[] | Human-readable diff vs previous version |
| `change_note` | string \| null | Optional note from publish |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 404 | Version not found, or not owned by this agent/org |
| 422 | Invalid UUID path params |

## Frontend notes

- **Restore into draft:** load this snapshot's fields into the editor, then [update-agent.md](update-agent.md) to save them as the draft — the version row itself stays immutable.
- To make this version live without editing, deploy it via [deploy-version.md](deploy-version.md).

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/version_detail.py`
- Use-case: `src/application/agents/use_cases/get_agent_version.py`
