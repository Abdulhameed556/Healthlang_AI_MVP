# PATCH /api/v1/knowledge-base/{kb_id}

## URL

**Path:** `/api/v1/knowledge-base/{kb_id}`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/{kb_id}` |
| Staging | `https://api.staging.afriex.io/api/v1/knowledge-base/{kb_id}` |
| Production | `https://api.afriex.io/api/v1/knowledge-base/{kb_id}` |

**See also:** [create-knowledge-base.md](create-knowledge-base.md), [delete-knowledge-base.md](delete-knowledge-base.md)

## Summary

Updates the name and/or description of a knowledge base container. Send only the fields you want to change — omitted fields are left unchanged.

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
| `kb_id` | UUID | The knowledge base to update. |

## Request body

```json
{
  "name": "Afriex Support FAQ v2",
  "description": "Updated knowledge base covering all product lines."
}
```

### Fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string \| null | No | New display name. 1–255 characters. |
| `description` | string \| null | No | New description. Pass `null` to clear it. |

At least one field should be provided, otherwise the request is a no-op.

## Success (200)

```json
{
  "message": "Knowledge base updated",
  "status_code": 200,
  "error": false,
  "data": null
}
```

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 403 | User's role does not have update permission |
| 404 | KB not found or not owned by the user's organisation |
| 422 | Field validation failure (e.g. empty name) |

## Frontend notes

- After a successful PATCH, refresh the KB detail view or list to show the updated name/description.
- This endpoint only updates the container metadata. To manage files inside the KB, use the entries endpoints.

## Code

- Endpoint: [backend/src/presentation/api/v1/knowledge_base/endpoints/update_kb.py](../../../../../backend/src/presentation/api/v1/knowledge_base/endpoints/update_kb.py)
- Use-case: `backend/src/application/knowledge_base/use_cases/update_knowledge_base.py`
