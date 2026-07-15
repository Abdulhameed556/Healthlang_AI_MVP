# Retrieval Pipeline

Converts a natural-language query into a ranked list of knowledge-base chunks relevant to a specific agent.

## Flow

```
query (str) + agent_id (UUID)
        │
        ▼
┌─────────────────┐
│  EmbedQueryStep │  OpenAI text-embedding-3-small → 1536-dim vector
└────────┬────────┘
         │ ctx.query_embedding
         ▼
┌──────────────────────────┐
│  SearchVectorStoreStep   │  Pinecone query filtered by agent_id → top-K matches
└────────┬─────────────────┘
         │ ctx.chunks
         ▼
  list[DocumentChunk]
```

## RetrievalContext fields

| Field | Type | Set by |
|---|---|---|
| `query` | `str` | caller |
| `agent_id` | `UUID` | caller |
| `top_k` | `int` (default 5) | caller |
| `query_embedding` | `list[float]` | EmbedQueryStep |
| `chunks` | `list[DocumentChunk]` | SearchVectorStoreStep |

## Usage

```python
from ai.src.application.retrieval.dependencies import build_retrieval_pipeline

pipeline = build_retrieval_pipeline()
chunks = await pipeline.retrieve(
    query="How do I reset my password?",
    agent_id=agent_id,
    top_k=5,
)
# chunks[i].text → inject into LLM prompt as context
```

## Agent scoping

Pinecone vectors are stored with `agent_id` in metadata (set during indexing). The search filter `{"agent_id": {"$eq": str(agent_id)}}` ensures an agent only retrieves chunks from its own linked knowledge bases, even when multiple agents share the same Pinecone index.

## Dependency wiring

`build_retrieval_pipeline()` in [dependencies.py](../../../ai/src/application/retrieval/dependencies.py) instantiates `OpenAIEmbedder` and `PineconeVectorStore` — the same concrete implementations used by the indexing pipeline.

## Not in v1

`RerankResultsStep` exists as a stub for future cross-encoder reranking. It is not wired into the pipeline.
