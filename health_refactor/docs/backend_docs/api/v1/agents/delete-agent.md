# DELETE /api/v1/agents/{agent_id}

## URL

**Path:** `/api/v1/agents/{agent_id}`

**Full URL:** `<base>/api/v1/agents/{agent_id}`

| Environment | Example full URL |
|-------------|------------------|
| Local | `http://localhost:8000/api/v1/agents/550e8400-e29b-41d4-a716-446655440000` |

**See also:** [agents README](README.md) · [list-agents.md](list-agents.md)

## Summary

Permanently deletes an agent and its owned rules, scenarios, version history, and attachment links.

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
| `agent_id` | UUID | Agent to delete |

## Request body

None.

## Success (200)

```json
{
  "message": "Agent deleted successfully",
  "status_code": 200,
  "error": false,
  "data": {
    "agent_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT / session |
| 403 | `read_only` caller |
| 404 | Agent not found or not in caller's organization |
| 422 | Invalid `agent_id` format |

## Frontend notes

- Confirm with the user before calling — deletion is irreversible.
- After success, remove the agent from local state and navigate to [list-agents.md](list-agents.md).

## Code

- Endpoint: `src/presentation/api/v1/agents/endpoints/delete.py`
- Use-case: `src/application/agents/use_cases/delete_agent.py`
