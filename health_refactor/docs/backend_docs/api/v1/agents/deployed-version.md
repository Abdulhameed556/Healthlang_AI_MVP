# GET /api/v1/agents/{agent_id}/deployed-version

## URL

**Path:** `/api/v1/agents/{agent_id}/deployed-version`

**Full URL:** `<base>/api/v1/agents/{agent_id}/deployed-version`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000/deployed-version` |

**See also:** [agents README](README.md) · [deploy-version.md](deploy-version.md) · [list-versions.md](list-versions.md) · [get-agent.md](get-agent.md)

## Summary

Returns the version snapshot currently **live** for customers (the agent's `deployed_version_id`). Responds **404** when the agent has no deployed version yet.

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
| `agent_id` | UUID | Agent whose live version to fetch |

## Success (200)

```json
{
  "message": "Deployed agent version retrieved successfully",
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
    "change_note": null
  }
}
```

`data` fields are identical to [get-version.md](get-version.md).

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 404 | Agent not found, **or the agent has no deployed version yet** |
| 422 | Invalid `agent_id` format |

## Frontend notes

- Use this to show "currently live" config independent of the editable draft ([get-agent.md](get-agent.md)).
- A 404 with an agent that exists means nothing has been deployed yet — render an empty/"not deployed" state rather than an error.

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/deployed_version.py`
- Use-case: `src/application/agents/use_cases/get_deployed_version.py`
