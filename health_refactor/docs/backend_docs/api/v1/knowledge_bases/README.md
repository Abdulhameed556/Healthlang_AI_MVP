# Knowledge Bases API (`/api/v1/knowledge-base`)

JWT-protected, organization-scoped routes for managing knowledge bases and their document entries. Entries are parsed, embedded, and stored in the vector store so the AI service can retrieve them during chat.

Send `Authorization: Bearer <access_token>` on every call. For multi-org users, optionally add `X-Organization-Id` — see [organization context](../auth/organization-context.md).

## Concepts

| Term | Description |
|------|-------------|
| **Knowledge Base (KB)** | A named container owned by an organization. One org can have many KBs. |
| **Entry** | A single document or text blob inside a KB. One KB can have many entries. |
| **Indexing** | The async pipeline that parses an entry, embeds it, and stores vectors so it can be searched. |
| **Agent attachment** | A link that lets a specific agent search a KB during chat retrieval. |

## Upload flow (file document)

The file upload is a three-step process that keeps large binaries off the backend:

```
1. POST /{kb_id}/entries/upload-url      → backend creates DB entry, returns presigned S3 PUT URL
2. Frontend PUTs file bytes directly to S3 (no backend involved)
3. POST /{kb_id}/entries/{entry_id}/confirm-upload → backend verifies S3, queues indexing
```

The AI worker then parses, embeds, and stores vectors. The entry's `indexing_status` moves: `processing` → `indexed` (or `failed`).

## Endpoints

| Method | Path | Doc | Description |
|--------|------|-----|-------------|
| GET | `/api/v1/knowledge-base/` | [list-knowledge-bases.md](list-knowledge-bases.md) | List all KBs for the org (paginated, with entry count and attached agents) |
| POST | `/api/v1/knowledge-base/` | [create-knowledge-base.md](create-knowledge-base.md) | Create a KB container |
| PATCH | `/api/v1/knowledge-base/{kb_id}` | [update-knowledge-base.md](update-knowledge-base.md) | Update KB name / description |
| DELETE | `/api/v1/knowledge-base/{kb_id}` | [delete-knowledge-base.md](delete-knowledge-base.md) | Delete KB and all its entries |
| POST | `/api/v1/knowledge-base/{kb_id}/entries/upload-url` | [generate-upload-url.md](generate-upload-url.md) | Step 1: create entry + get presigned S3 URL |
| POST | `/api/v1/knowledge-base/{kb_id}/entries/{entry_id}/confirm-upload` | [confirm-upload.md](confirm-upload.md) | Step 2: verify S3 upload, queue indexing |
| GET | `/api/v1/knowledge-base/{kb_id}/entries` | [list-entries.md](list-entries.md) | List entries with pagination, search, and status filter (includes `kb_name`/`kb_description`) |
| PATCH | `/api/v1/knowledge-base/{kb_id}/entries/{entry_id}` | — | Lifecycle action on an entry: `archive`, `unarchive`, or `retry` |
| DELETE | `/api/v1/knowledge-base/{kb_id}/entries/{entry_id}` | [delete-entry.md](delete-entry.md) | Hard-delete entry (removes file + vectors) |
| POST | `/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` | [attach-agent.md](attach-agent.md) | Link an agent to this KB |
| DELETE | `/api/v1/knowledge-base/{kb_id}/agents/{agent_id}` | [detach-agent.md](detach-agent.md) | Unlink an agent from this KB |

## Supported file types

| Value | MIME type to use in S3 PUT |
|-------|----------------------------|
| `docx` | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |
| `md` | `text/markdown` |
| `txt` | `text/plain` |

PDF is **not** supported in v1.

## `indexing_status` values

| Value | Meaning |
|-------|---------|
| `processing` | Entry is queued or actively being processed |
| `indexed` | Embeddings stored in vector store; entry is searchable |
| `failed` | Processing failed; use the `retry` action to re-queue |

## Response envelope

All endpoints return the standard envelope:

```json
{
  "message": "…",
  "status_code": 200,
  "error": false,
  "data": {}
}
```

On failure, `error` is `true` and `data` is typically `null`.

## File size limit

Maximum **15 MB** per file. Enforce this on the frontend before calling `upload-url`. The backend does not validate file size.

## Related

- [../agents/README.md](../agents/README.md) — agents that reference knowledge bases
- [../auth/login.md](../auth/login.md) — how to get the Bearer token
- [../../../../ai_docs/api/v1/retrieval-evaluation/README.md](../../../../ai_docs/api/v1/retrieval-evaluation/README.md) — evaluate retrieval quality for KB entries
