# POST /api/v1/knowledge-base/

## URL

**Path:** `/api/v1/knowledge-base/`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/` |
| Staging | `https://api.staging.afriex.io/api/v1/knowledge-base/` |
| Production | `https://api.afriex.io/api/v1/knowledge-base/` |

**See also:** [README.md](README.md) — full KB flow overview

## Summary

Creates an empty knowledge base container belonging to the authenticated user's organisation. The KB container holds entries (documents). After creating the KB, add entries via the [upload-url flow](generate-upload-url.md) or [create-text-entry](create-text-entry.md).

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|---------|
| `super_admin` | Yes |
| `admin` | Yes |
| `agent` | No |

## Request body

```json
{
  "name": "Customer Support FAQ",
  "description": "Frequently asked questions about our products and policies."
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | Yes | Display name. 1–255 characters. |
| `description` | string \| null | No | Optional purpose description. |

## Success (201)

```json
{
  "message": "Knowledge base created",
  "status_code": 201,
  "error": false,
  "data": {
    "kb_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Customer Support FAQ"
  }
}
```

| Field | Notes |
|-------|-------|
| `data.kb_id` | UUID of the newly created knowledge base. Store this — you need it for all subsequent KB calls. |
| `data.name` | The name as saved. |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 403 | Authenticated user's role does not have create permission |
| 422 | Validation error (`name` missing or exceeds 255 chars) |

## Frontend notes

- After creating the KB, immediately show it in the KB list and proceed to the upload flow.
- The `kb_id` must be stored locally for the duration of the upload session.
- There is no limit on the number of KBs per organisation in v1.

## Code

- Endpoint: [backend/src/presentation/api/v1/knowledge_base/endpoints/create.py](../../../../../backend/src/presentation/api/v1/knowledge_base/endpoints/create.py)
- Use-case: `backend/src/application/knowledge_base/use_cases/create_knowledge_base.py`
