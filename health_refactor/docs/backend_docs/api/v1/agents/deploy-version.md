# POST /api/v1/agents/{agent_id}/versions/{version_id}/deploy

## URL

**Path:** `/api/v1/agents/{agent_id}/versions/{version_id}/deploy`

**Full URL:** `<base>/api/v1/agents/{agent_id}/versions/{version_id}/deploy`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000/versions/550e8400-e29b-41d4-a716-446655440010/deploy` |

**See also:** [agents README](README.md) · [publish-agent.md](publish-agent.md) · [list-versions.md](list-versions.md) · [deployed-version.md](deployed-version.md)

## Summary

Promotes an **existing published version** to be the **live** snapshot customers hit, sets agent status to `deployed`, and **invalidates the runtime cache** so the change takes effect immediately.

Deploy never creates a version — [publish-agent.md](publish-agent.md) does that. Use deploy to go live with a freshly published version or to **roll back** to an older one.

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
| `agent_id` | UUID | Agent to update |
| `version_id` | UUID | Existing version from [list-versions.md](list-versions.md) |

## Request body

None.

## Success (200)

```json
{
  "message": "Agent version deployed successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "version": {
      "version_id": "550e8400-e29b-41d4-a716-446655440010",
      "agent_id": "550e8400-e29b-41d4-a716-446655440000",
      "version_number": 2,
      "configuration_snapshot": { },
      "created_at": "2026-06-04T13:00:00Z",
      "created_by": "550e8400-e29b-41d4-a716-446655440050",
      "changes_applied": ["Brand voice prompt updated"],
      "change_note": null
    },
    "agent_status": "deployed"
  }
}
```

### `data` fields

| Field | Type | Description |
|-------|------|-------------|
| `version.version_id` | UUID | Version now live |
| `version.version_number` | integer | Sequence number of that snapshot |
| `version.configuration_snapshot` | object | Immutable config now used at runtime |
| `version.created_by` / `changes_applied` / `change_note` | — | Carried from publish; see [publish-agent.md](publish-agent.md) |
| `agent_status` | string | Always `deployed` after success |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Agent not found, version not found, or version not owned by this agent/org |
| 422 | Invalid UUID path params |

## Frontend notes

- **Go live:** publish first ([publish-agent.md](publish-agent.md)), then deploy the returned `version_id`.
- **Rollback:** pick any row from [list-versions.md](list-versions.md) and deploy its `version_id`. `version_number` does not increment.
- **Draft unchanged:** [get-agent.md](get-agent.md) still returns the editable draft; deploying does not revert unsaved draft edits.
- After success, the deployed version is reflected by `is_deployed` in [list-versions.md](list-versions.md) and by [deployed-version.md](deployed-version.md).

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/deploy_version.py`
- Use-case: `src/application/agents/use_cases/deploy_version.py`
