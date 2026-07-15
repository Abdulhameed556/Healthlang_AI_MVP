"""Dramatiq tasks: ingest and delete knowledge-base documents in Pinecone."""
from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from uuid import UUID

import dramatiq

from ai.src.infrastructure.workers._base import log_task_end, log_task_start

INGEST_TASK_NAME = "ingest_document"
DELETE_TASK_NAME = "delete_document"


@dataclass(frozen=True)
class IngestDocumentInput:
    """Data the ingest task needs to run."""

    kb_entry_id: str


@dataclass(frozen=True)
class IngestDocumentResult:
    """Data the ingest task produces."""

    outcome: str
    kb_entry_id: str


@dataclass(frozen=True)
class DeleteDocumentInput:
    """Data the delete task needs to run."""

    kb_entry_id: str


@dataclass(frozen=True)
class DeleteDocumentResult:
    """Data the delete task produces."""

    outcome: str
    kb_entry_id: str


@dramatiq.actor(max_retries=3)
def ingest_document(kb_entry_id: str) -> None:
    payload = IngestDocumentInput(kb_entry_id=kb_entry_id)
    log_task_start(INGEST_TASK_NAME, asdict(payload))

    async def _run() -> None:
        from backend.src.infrastructure.database.session import engine
        # asyncio.run() creates a new loop each call; stale asyncpg connections
        # from a previous loop fail pool_pre_ping. dispose() empties the pool
        # so fresh connections are created inside the current loop.
        await engine.dispose(close=False)

        from ai.src.application.indexing.dependencies import build_indexing_pipeline
        pipeline = build_indexing_pipeline()
        await pipeline.run(kb_entry_id)

    asyncio.run(_run())
    log_task_end(INGEST_TASK_NAME, asdict(IngestDocumentResult(outcome="processed", kb_entry_id=kb_entry_id)))


@dramatiq.actor(max_retries=3)
def delete_document(kb_entry_id: str) -> None:
    """Remove all Pinecone vectors that belong to a KB entry."""
    payload = DeleteDocumentInput(kb_entry_id=kb_entry_id)
    log_task_start(DELETE_TASK_NAME, asdict(payload))

    async def _run() -> None:
        from backend.src.infrastructure.database.session import engine
        await engine.dispose(close=False)

        from ai.src.infrastructure.vector_store.pinecone import PineconeVectorStore
        await PineconeVectorStore().delete_by_kb_entry(UUID(kb_entry_id))

    asyncio.run(_run())
    log_task_end(DELETE_TASK_NAME, asdict(DeleteDocumentResult(outcome="deleted", kb_entry_id=kb_entry_id)))
