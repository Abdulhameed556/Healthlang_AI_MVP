# POST /api/v1/knowledge-base/{kb_id}/agents/{agent_id}

## URL

**Path:** `/api/v1/knowledge-base/{kb_id}/agents/{agent_id}`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` |
| Staging | `https://api.staging.afriex.io/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` |
| Production | `https://api.afriex.io/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` |

**See also:** [detach-agent.md](detach-agent.md), [list-entries.md](list-entries.md) — `attached_agents` field in entries response

## Summary

Links an agent to a knowledge base. Once attached, the agent's retrieval pipeline will search the KB's indexed entries during chat to provide relevant context.

Both the agent and the knowledge base must belong to the same organisation. Calling this endpoint when the agent is already attached is **idempotent** — it returns 200 without error.

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
| `kb_id` | UUID | The knowledge base to attach to. |
| `agent_id` | UUID | The agent to link. |

## Request body

None. All information is in the path.

## Success (200)

```json
{
  "message": "Agent attached",
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

- After a successful attach, update the local state to reflect the new agent in the KB's `attached_agents` list (or re-fetch the entry list).
- This endpoint is safe to call on mount as an "ensure-attached" operation — the idempotency means duplicate calls are harmless.
- An agent can be attached to multiple KBs simultaneously; each KB's entries are all available to the agent.

## Code

- Endpoint: [backend/src/presentation/api/v1/knowledge_base/endpoints/attach.py](../../../../../backend/src/presentation/api/v1/knowledge_base/endpoints/attach.py)
- Use-case: `backend/src/application/knowledge_base/use_cases/attach_to_agent.py`
