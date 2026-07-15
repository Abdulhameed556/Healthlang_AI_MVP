# POST /api/v1/agents/{agent_id}/publish

## URL

**Path:** `/api/v1/agents/{agent_id}/publish`

**Full URL:** `<base>/api/v1/agents/{agent_id}/publish`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000/publish` |

**See also:** [agents README](README.md) · [deploy-version.md](deploy-version.md) · [list-versions.md](list-versions.md) · [update-agent.md](update-agent.md)

## Summary

Freezes the agent's **current draft** as a **new immutable version** (`v1`, `v2`, …), records **who** published it and a backend-computed, human-readable **`changes_applied`** diff against the previous version. An optional free-text `change_note` can be attached.

Publishing does **NOT** go live. The runtime keeps serving whatever version is currently deployed. Promote a published version to live separately with [deploy-version.md](deploy-version.md).

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
| `agent_id` | UUID | Agent whose draft to publish |

## Request body

Optional. Omit entirely or send:

```json
{
  "change_note": "Tightened privacy rule wording before rollout."
}
```

| Field | Type | Required | Limits |
|-------|------|----------|--------|
| `change_note` | string \| null | no | max 1000; free-text reason for this version |

## Success (201)

```json
{
  "message": "Agent version published successfully",
  "status_code": 201,
  "error": false,
  "data": {
    "version": {
      "version_id": "550e8400-e29b-41d4-a716-446655440010",
      "agent_id": "550e8400-e29b-41d4-a716-446655440000",
      "version_number": 2,
      "configuration_snapshot": { },
      "created_at": "2026-06-04T13:00:00Z",
      "created_by": "550e8400-e29b-41d4-a716-446655440050",
      "changes_applied": [
        "Brand voice prompt updated",
        "Rule 'Privacy' updated"
      ],
      "change_note": "Tightened privacy rule wording before rollout."
    },
    "agent_status": "inactive"
  }
}
```

### `data` fields

| Field | Type | Description |
|-------|------|-------------|
| `version.version_id` | UUID | New immutable version record id |
| `version.version_number` | integer | Monotonic per agent (1, 2, 3, …) |
| `version.configuration_snapshot` | object | Full config frozen at publish time; same nested shape as [get-agent.md](get-agent.md) |
| `version.created_at` | ISO 8601 datetime | When this version was published |
| `version.created_by` | UUID \| null | User who published (the authenticated caller) |
| `version.changes_applied` | string[] | Backend-computed human-readable diff vs the previous version; `["Initial version published"]` for the first |
| `version.change_note` | string \| null | Optional note from the request body |
| `agent_status` | string | Unchanged by publish (`inactive` until a version is deployed) |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Agent not found or not in caller's organization |
| 422 | Invalid `agent_id`, or `change_note` over 1000 chars |

## Frontend notes

- Save pending edits via [update-agent.md](update-agent.md) **before** publishing.
- `changes_applied` is computed by the backend — do **not** send it from the client.
- Publishing alone does not affect customers. Show a separate **Deploy** action ([deploy-version.md](deploy-version.md)) to go live.
- After publish, refresh the history list ([list-versions.md](list-versions.md)).

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/publish.py`
- Use-case: `src/application/agents/use_cases/publish_agent.py`
- Diff: `src/application/agents/version_diff.py`
