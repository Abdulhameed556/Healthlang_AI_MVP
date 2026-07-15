# DELETE /api/v1/knowledge-base/{kb_id}

## URL

**Path:** `/api/v1/knowledge-base/{kb_id}`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/{kb_id}` |
| Staging | `https://api.staging.afriex.io/api/v1/knowledge-base/{kb_id}` |
| Production | `https://api.afriex.io/api/v1/knowledge-base/{kb_id}` |

**See also:** [delete-entry.md](delete-entry.md) — delete a single entry, [detach-agent.md](detach-agent.md) — unlink agents without deleting

## Summary

Permanently deletes an entire knowledge base and everything it contains:

1. Deletes all database records for the KB and all its entries.
2. Deletes all source files from S3.
3. Dispatches background tasks to purge all vectors for every entry from the vector store.
4. Removes all agent attachments.

**This action cannot be undone.** All entries, files, and vectors are destroyed. If you only want to unlink an agent from this KB without destroying data, use [detach-agent](detach-agent.md) instead.

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
| `kb_id` | UUID | The knowledge base to delete. |

## Request body

None.

## Success (200)

```json
{
  "message": "Knowledge base deleted",
  "status_code": 200,
  "error": false,
  "data": null
}
```

Vector purges for individual entries run asynchronously in the background. The HTTP response returns as soon as the DB records are removed.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 403 | User's role does not have delete permission |
| 404 | KB not found or not owned by the user's organisation |

## Frontend notes

- Show a confirmation dialog with a clear warning ("This will permanently delete the knowledge base and all N documents") before calling this endpoint.
- After a 200 response, remove the KB from the local KB list immediately (optimistic update).
- Any agents that were attached to this KB will automatically lose access to its content — no separate detach calls are needed.

## Code

- Endpoint: [backend/src/presentation/api/v1/knowledge_base/endpoints/delete_kb.py](../../../../../backend/src/presentation/api/v1/knowledge_base/endpoints/delete_kb.py)
- Use-case: `backend/src/application/knowledge_base/use_cases/delete_knowledge_base.py`
