# Ingest Document — Dramatiq Background Task

## Overview

`ingest_document` is a [Dramatiq](https://dramatiq.io/) background actor that processes
one knowledge-base entry through the full indexing pipeline asynchronously.

This is **not an HTTP endpoint**. It is enqueued directly from the backend confirm-upload
use-case via an in-process call (both services run in the same process under `run.py`).

**See also:** [indexing pipeline](../../../pipelines/indexing.md)

## Trigger

The backend's **confirm-upload** use-case enqueues the task after verifying the file
exists in S3:

```python
# backend/src/application/knowledge_base/use_cases/confirm_upload.py
from ai.src.infrastructure.workers.tasks.indexing import ingest_document
ingest_document.send(str(entry.id))
```

## Signature

```python
@dramatiq.actor(max_retries=3)
def ingest_document(kb_entry_id: str) -> None: ...
```

| Parameter | Type | Notes |
|-----------|------|-------|
| `kb_entry_id` | `str` (UUID) | Primary key of the `knowledge_base_entries` row to process. |

## Pipeline steps

| # | Step | Code |
|---|------|------|
| 1 | Download file from S3 | `ai/src/infrastructure/storage/s3.py` |
| 2 | Parse document text | `ai/src/infrastructure/document_processing/` |
| 3 | Chunk text into overlapping windows | `ai/src/infrastructure/document_processing/chunker.py` |
| 4 | Embed chunks via OpenAI | `ai/src/infrastructure/llm/` |
| 5 | Upsert vectors to Pinecone | `ai/src/infrastructure/vector_store/pinecone.py` |
| 6 | PATCH entry status → `indexed` | backend HTTP via `BACKEND_INTERNAL_API_KEY` |

Steps 2–6 are Phase 4–6 work. Phase 2 registers the actor as a no-op stub.

## Retry behaviour

Dramatiq retries up to **3 times** with exponential back-off on any unhandled exception.
If all retries are exhausted the message moves to the dead-letter queue.
The DB row remains in `processing` status until step 6 completes.

## Broker

| Setting | Default | Env var |
|---------|---------|---------|
| Broker | Redis | `DRAMATIQ_BROKER_URL` (falls back to `REDIS_URL`) |
| Queue | `default` | — |

In tests, the root `tests/conftest.py` registers a `StubBroker` so no real Redis
connection is needed.

## Code

- Actor: `ai/src/infrastructure/workers/tasks/indexing.py`
- Broker config: `ai/src/infrastructure/workers/broker.py`
- S3 download: `ai/src/infrastructure/storage/s3.py`
