# GET /api/v1/knowledge-base/{kb_id}/entries

## URL

**Path:** `/api/v1/knowledge-base/{kb_id}/entries`

| Environment | Example full URL |
|-------------|-----------------|
| Local | `http://localhost:8000/api/v1/knowledge-base/{kb_id}/entries` |
| Staging | `https://api.staging.afriex.io/api/v1/knowledge-base/{kb_id}/entries` |
| Production | `https://api.afriex.io/api/v1/knowledge-base/{kb_id}/entries` |

**See also:** [README.md](README.md), [delete-entry.md](delete-entry.md)

## Summary

Returns a paginated list of document entries in a knowledge base. Supports filtering by name substring, indexing status, and archived state. Each entry includes the list of agents currently attached to the parent knowledge base (same for all entries in the same KB), as well as the parent KB's `name` and `description` so the frontend can display full context without a separate KB fetch.

The knowledge base must belong to the authenticated user's organisation.

## Auth

```http
Authorization: Bearer <access_token>
```

| Role | Can call |
|------|---------|
| `super_admin` | Yes |
| `admin` | Yes |
| `agent` | Yes |

## Path parameters

| Parameter | Type | Notes |
|-----------|------|-------|
| `kb_id` | UUID | The knowledge base to list entries from. |

## Query parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `search` | string | — | Filter entries whose `name` contains this substring (case-insensitive). |
| `status` | string | — | Filter by `indexing_status`: `processing`, `indexed`, or `failed`. |
| `archived` | boolean | `false` | Set to `true` to include archived (soft-deleted) entries. |
| `page` | integer | `1` | 1-based page number. |
| `page_size` | integer | `20` | Entries per page. Min 1, max 100. |

## Success (200)

```json
{
  "message": "Entries retrieved",
  "status_code": 200,
  "error": false,
  "data": {
    "items": [
      {
        "id": "aaaaaaaa-aaaa-4000-8000-aaaaaaaaaaaa",
        "name": "Refund Policy.docx",
        "description": "Our complete refund and returns policy document.",
        "file_type": "docx",
        "file_size_bytes": 45056,
        "indexing_status": "indexed",
        "is_archived": false,
        "created_at": "2025-01-15T10:30:00Z",
        "updated_at": "2025-01-15T10:35:22Z",
        "kb_name": "Afriex Support FAQ",
        "kb_description": "Frequently asked questions about our products and policies.",
        "attached_agents": [
          {
            "agent_id": "dddddddd-dddd-4000-8000-dddddddddddd",
            "name": "Support Bot"
          }
        ]
      }
    ],
    "total": 42,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

### `data` fields

| Field | Notes |
|-------|-------|
| `items` | Array of entry objects for this page. |
| `total` | Total matching entries across all pages. |
| `page` | Current page (1-based). |
| `page_size` | Requested page size. |
| `total_pages` | `ceil(total / page_size)`. 0 when there are no entries. |

### Entry object fields

| Field | Notes |
|-------|-------|
| `id` | UUID of the entry. |
| `name` | Filename or display name. |
| `description` | Optional human-readable description of the document's contents. |
| `file_type` | `docx`, `md`, or `txt`. |
| `file_size_bytes` | Original file size. `null` for text entries created inline. |
| `indexing_status` | `processing` — being indexed; `indexed` — searchable; `failed` — error. |
| `is_archived` | `true` when the entry has been soft-deleted. |
| `created_at` | ISO 8601 UTC timestamp. |
| `updated_at` | ISO 8601 UTC timestamp. |
| `kb_name` | Display name of the parent knowledge base. |
| `kb_description` | Description of the parent knowledge base. `null` if not set. |
| `attached_agents` | Agents currently linked to the parent KB. Same for every entry in the KB. |

## Errors

| Status | When |
|--------|------|
| 401 | Missing or invalid JWT |
| 404 | KB not found or does not belong to the user's organisation |
| 422 | Invalid query parameter types or values |

## Frontend notes

- Poll this endpoint every few seconds after an upload to track `indexing_status` changes from `processing` → `indexed` (or `failed`).
- Use `archived=true` to build a "trash" / recovery view.
- The `attached_agents` list is the same on every entry in the KB — it reflects the KB's attachments, not the individual entry's.
- When `total_pages` is 0 (no entries), render an empty state rather than showing pagination.
- On retry flow: after calling `PATCH` with `action=retry`, re-fetch this list to confirm the entry moves back to `processing`.

## Code

- Endpoint: [backend/src/presentation/api/v1/knowledge_base/endpoints/list.py](../../../../../backend/src/presentation/api/v1/knowledge_base/endpoints/list.py)
- Use-case: `backend/src/application/knowledge_base/use_cases/list_entries.py`
