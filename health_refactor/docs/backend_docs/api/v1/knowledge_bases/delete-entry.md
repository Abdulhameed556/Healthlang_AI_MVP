# DELETE /api/v1/knowledge-base/{kb_id}/entries/{entry_id}

## URL

**Path:** `/api/v1/knowledge-base/{kb_id}/entries/{entry_id}`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries/{entry_id}` |
| Staging | `https://api.staging.afriex.io/api/v1/knowledge-base/{kb_id}/entries/{entry_id}` |
| Production | `https://api.afriex.io/api/v1/knowledge-base/{kb_id}/entries/{entry_id}` |

**See also:** [update-entry.md](update-entry.md) — soft-delete (archive) without purging vectors, [delete-knowledge-base.md](delete-knowledge-base.md) — delete the entire KB

## Summary

Permanently and irreversibly deletes a single knowledge base entry. The operation:

1. Deletes the database record.
2. Deletes the source file from S3.
3. Dispatches a background task to purge the entry's vectors from the vector store.

**This action cannot be undone.** If you only want to hide the entry from the UI without removing vectors (e.g., temporary removal), use `PATCH` with `action=archive` instead.

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
| `kb_id` | UUID | The parent knowledge base. |
| `entry_id` | UUID | The entry to delete. |

## Request body

None.

## Success (200)

```json
{
  "message": "Entry deleted",
  "status_code": 200,
  "error": false,
  "data": null
}
```

The vector purge runs asynchronously in the background — the entry is immediately removed from the DB and S3, and the HTTP response returns without waiting for vector deletion to complete.

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 403 | User's role does not have delete permission |
| 404 | Entry or KB not found, or not owned by the user's organisation |

## Frontend notes

- Show a confirmation dialog before calling this endpoint — the action is permanent.
- Remove the entry from the local list immediately after a 200 response (optimistic update).
- Consider offering the "archive" action first in the UI (`PATCH action=archive`) with delete as a secondary destructive option.
- Vector purge completes in the background; no polling is needed — the entry is gone from search results immediately once the DB record is deleted.

## Code

- Endpoint: [backend/src/presentation/api/v1/knowledge_base/endpoints/delete.py](../../../../../backend/src/presentation/api/v1/knowledge_base/endpoints/delete.py)
- Use-case: `backend/src/application/knowledge_base/use_cases/delete_entry.py`
