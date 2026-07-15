# DELETE /api/v1/knowledge-base/{kb_id}/agents/{agent_id}

## URL

**Path:** `/api/v1/knowledge-base/{kb_id}/agents/{agent_id}`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` |
| Staging | `https://api.staging.afriex.io/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` |
| Production | `https://api.afriex.io/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` |

**See also:** [attach-agent.md](attach-agent.md), [delete-knowledge-base.md](delete-knowledge-base.md)

## Summary

Removes the link between an agent and a knowledge base. The knowledge base and all its entries are **not** deleted; the agent simply stops searching this KB during chat retrieval.

Calling this endpoint when the agent is not currently attached is a **no-op** — it returns 200 without error.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|---------|
| `super_admin` | Yes |
| `admin` | Yes |
| `agent` | No |

## Path parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `kb_id` | UUID | The knowledge base to detach from. |
| `agent_id` | UUID | The agent to unlink. |

## Request body

None. All information is in the path.

## Success (200)

```json
{
  "message": "Agent detached",
  "status_code": 200,
  "error": false,
  "data": null
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 403 | User's role does not have permission |
| 404 | KB or agent not found, or either does not belong to the user's organisation |

## Frontend notes

- After a successful detach, remove the agent from the KB's `attached_agents` list in local state (or re-fetch the entry list).
- The KB and all its entries remain intact and can be re-attached to another agent at any time.
- The agent continues to work normally — it just won't search this particular KB anymore.

## Code

- Endpoint: [backend/src/presentation/api/v1/knowledge_base/endpoints/detach.py](../../../../../backend/src/presentation/api/v1/knowledge_base/endpoints/detach.py)
- Use-case: `backend/src/application/knowledge_base/use_cases/detach_from_agent.py`
