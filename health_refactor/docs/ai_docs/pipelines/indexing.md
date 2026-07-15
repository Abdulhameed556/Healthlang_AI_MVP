# Indexing Pipeline

Runs as a Dramatiq background task (`ingest_document`) after the backend confirms a KB file upload.

**See also:** [ingest_document task](../api/v1/internal/ingest.md) · [Pinecone ADR](../architecture/adr/005-pinecone-for-vectors.md)

---

## Trigger flow

```
Frontend PUT  → S3 (direct presigned upload)
Frontend POST → /api/v1/knowledge-bases/{kb_id}/entries/{entry_id}/confirm-upload
Backend ConfirmUpload use-case → ingest_document.send(str(entry_id))
Dramatiq worker picks message → ingest_document() → asyncio.run(pipeline.run(entry_id))
```

The Dramatiq worker runs in a separate process (`make worker`) but shares the same Python
environment and Postgres connection pool as the main app.

---

## IndexingContext fields

All pipeline state lives in a single `IndexingContext` dataclass
(`ai/src/application/indexing/context.py`):

| Field | Type | Set by |
|-------|------|--------|
| `kb_entry_id` | `UUID` | pipeline loader |
| `knowledge_base_id` | `UUID` | pipeline loader |
| `organization_id` | `UUID` | pipeline loader (via `knowledge_bases` table) |
| `agent_ids` | `list[UUID]` | pipeline loader (via `agent_knowledge_base` join table) |
| `storage_path` | `str` | pipeline loader |
| `file_type` | `str` | pipeline loader |
| `raw_bytes` | `bytes` | `FetchDocumentStep` |
| `text` | `str` | `ParseDocumentStep` |
| `chunk_texts` | `list[str]` | `ChunkTextStep` |
| `embeddings` | `list[list[float]]` | `EmbedChunksStep` |
| `failed` | `bool` | set to `True` on any step exception |
| `error` | `str` | exception message on failure |

---

## Steps

| # | Class | File | Description |
|---|-------|------|-------------|
| 1 | `FetchDocumentStep` | `steps/fetch_document.py` | Download raw file bytes from S3 |
| 2 | `ParseDocumentStep` | `steps/parse_document.py` | Route to DOCX / TXT / MD parser via `ParserFactory` |
| 3 | `ChunkTextStep` | `steps/chunk_text.py` | Split into 500-token chunks, 50-token overlap (tiktoken cl100k_base) |
| 4 | `EmbedChunksStep` | `steps/embed_chunks.py` | Batch embed with `text-embedding-3-small` via OpenAI |
| 5 | `UpsertVectorsStep` | `steps/upsert_vectors.py` | Write `DocumentChunk` records to Pinecone — one chunk per linked agent |
| 6 | `NotifyBackendStep` | `steps/notify_backend.py` | Direct DB update: `indexing_status = "indexed"` or `"failed"` |

### Step 5 — agent scoping

`UpsertVectorsStep` queries the `agent_knowledge_base` join table to find all agents linked
to this KB. For each `(agent_id, chunk_index)` pair it creates a `DocumentChunk` with
`chunk_id = "{kb_entry_id}_{chunk_index}_{agent_id}"`. This lets Pinecone filter by
`agent_id` at query time. If the KB has no agents linked yet, the upsert is skipped —
vectors will be stored when an agent is attached (Phase 6).

### Step 6 — direct DB write (not HTTP)

`NotifyBackendStep` imports `async_session_factory` from
`backend.src.infrastructure.database.session` and updates `KnowledgeBaseEntry.indexing_status`
directly. This avoids an unnecessary HTTP round-trip since the worker already has DB access.

---

## Pinecone vector metadata

Each vector stored in Pinecone carries:

```json
{
  "kb_entry_id": "<uuid>",
  "agent_id": "<uuid>",
  "organization_id": "<uuid>",
  "text": "<chunk text>"
}
```

Additional metadata keys from `DocumentChunk.metadata` are merged in if present.

---

## Error handling

- The pipeline catches any step exception, sets `ctx.failed = True`, and always runs
  `NotifyBackendStep` last so the DB status is updated to `"failed"`.
- Dramatiq retries the whole task up to 3 times on any unhandled exception that escapes
  the pipeline (e.g. a DB connection failure in the loader or the notify step itself).
- Pinecone upsert is idempotent — re-running overwrites vectors with the same `chunk_id`.

---

## Dependency wiring

`ai/src/application/indexing/dependencies.py` exports `build_indexing_pipeline()`, which
constructs the pipeline with all concrete implementations:

```
session_factory → backend.src.infrastructure.database.session.async_session_factory
embedder        → OpenAIEmbedder   (infrastructure/llm/embedder.py)
vector_store    → PineconeVectorStore (infrastructure/vector_store/pinecone.py)
parser_factory  → ParserFactory    (infrastructure/document_processing/parser_factory.py)
chunker         → TiktokenChunker  (infrastructure/document_processing/chunker.py)
```

---

## Supported file types

| Type | Parser |
|------|--------|
| `txt` | `TextParser` — UTF-8 decode |
| `md` | `TextParser` — UTF-8 decode (raw markdown is embedded directly) |
| `docx` | `DocxParser` — `python-docx` paragraph extraction |

PDF is **not supported** in v1.
