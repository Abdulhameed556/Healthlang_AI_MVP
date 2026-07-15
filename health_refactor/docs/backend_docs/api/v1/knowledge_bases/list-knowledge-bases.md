# GET /api/v1/knowledge-base/

## URL

**Path:** `/api/v1/knowledge-base/`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/` |
| Staging | `https://api.staging.afriex.io/api/v1/knowledge-base/` |
| Production | `https://api.afriex.io/api/v1/knowledge-base/` |

**See also:** [create-knowledge-base.md](create-knowledge-base.md), [list-entries.md](list-entries.md)

## Summary

Returns a paginated list of all knowledge bases belonging to the authenticated user's organisation. Each item includes the KB's metadata, the count of active (non-archived) entries inside it, and the agents currently attached to it.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|---------|
| `super_admin` | Yes |
| `admin` | Yes |
| `agent` | No |

## Query parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `page` | integer | 1 | Page number (1-based). |
| `page_size` | integer | 20 | Items per page. Max 100. |

## Success (200)

```json
{
  "message": "Knowledge bases retrieved",
  "status_code": 200,
  "error": false,
  "data": {
    "items": [
      {
        "kb_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Afriex Support FAQ",
        "description": "Frequently asked questions about our products and policies.",
        "entry_count": 12,
        "attached_agents": [
          {
            "agent_id": "bbbbbbbb-bbbb-4000-8000-bbbbbbbbbbbb",
            "name": "Support Bot"
          }
        ],
        "created_at": "2026-01-15T10:00:00Z",
        "updated_at": "2026-06-01T08:30:00Z"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### Response fields

| Field | Type | Description |
|-------|------|-------------|
| `kb_id` | UUID | Unique identifier of the knowledge base. |
| `name` | string | Display name. |
| `description` | string \| null | Optional description. |
| `entry_count` | integer | Number of active (non-archived) entries in this KB. |
| `attached_agents` | array | Agents currently linked to this KB. |
| `created_at` | ISO 8601 | When the KB was created. |
| `updated_at` | ISO 8601 | When the KB was last updated. |
| `total` | integer | Total KBs in the organisation (across all pages). |
| `total_pages` | integer | Number of pages at the current `page_size`. |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 403 | User's role does not have read permission |

## Frontend notes

- Use this endpoint to render the "All Knowledge Bases" screen.
- `entry_count` reflects active entries only — archived entries are excluded.
- To see the entries inside a specific KB, call `GET /{kb_id}/entries`.

## Code

- Endpoint: [backend/src/presentation/api/v1/knowledge_base/endpoints/list_kbs.py](../../../../../backend/src/presentation/api/v1/knowledge_base/endpoints/list_kbs.py)
- Use-case: `backend/src/application/knowledge_base/use_cases/list_knowledge_bases.py`
