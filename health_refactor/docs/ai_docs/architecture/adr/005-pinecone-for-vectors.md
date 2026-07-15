# ADR-005 — Use Pinecone for Vector Storage

**Status:** Accepted  
**Supersedes:** [ADR-004 — pgvector for RAG](004-pgvector-for-rag.md)

## Context

ADR-004 chose pgvector (Postgres extension) for storing document embeddings. As the
project moved from prototype to implementation, two blockers emerged:

1. **Operational overhead** — pgvector requires provisioning a Postgres instance with
   the `vector` extension, running Alembic migrations for the `document_chunks` table,
   and maintaining a separate DB connection pool from the application DB.
2. **Free-tier availability** — Pinecone offers a free serverless index with no
   infrastructure to manage, which better matches the project's current stage.

## Decision

Switch vector storage from pgvector to **Pinecone** (serverless, free tier).

## Implementation

| Component | Path |
|-----------|------|
| Store class | `ai/src/infrastructure/vector_store/pinecone.py` |
| Interface | `ai/src/domain/knowledge_base/interfaces.py` — `IVectorStore` unchanged |
| Config | `PINECONE_API_KEY`, `PINECONE_INDEX_NAME` in `ai/src/core/config.py` |

`PineconeVectorStore` wraps the synchronous Pinecone Python SDK in
`asyncio.to_thread()` calls, matching the pattern used for boto3 S3 operations.

### Metadata stored per vector

```json
{
  "kb_entry_id": "<uuid>",
  "agent_id":    "<uuid>",
  "organization_id": "<uuid>",
  "text":        "<chunk text>"
}
```

Search filters on `agent_id` so a query for one agent never surfaces another
agent's documents.

## Consequences

- **Positive:** No DB migration needed for vector storage; free tier covers MVP scale;
  Pinecone handles index replication and sharding automatically.
- **Negative:** Vectors now live in an external SaaS (Pinecone) rather than the
  application DB — requires `PINECONE_API_KEY` in production env.
- **Neutral:** `IVectorStore` protocol is unchanged so swapping back to pgvector (or
  any other store) requires only a new implementation class.

## Required env vars

| Var | Example | Notes |
|-----|---------|-------|
| `PINECONE_API_KEY` | `pcsk_...` | From Pinecone console |
| `PINECONE_INDEX_NAME` | `supportos` | Must be created in Pinecone dashboard first |
