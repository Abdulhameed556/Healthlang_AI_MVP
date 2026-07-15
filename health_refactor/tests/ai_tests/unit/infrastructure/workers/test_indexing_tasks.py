"""Unit tests: ai/src/infrastructure/workers/tasks/indexing.py"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

_KB_ENTRY_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _fake_asyncio_run(coro):
    """Run a coroutine in a fresh event loop (avoids nesting with pytest-asyncio)."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(coro)
    finally:
        loop.close()


def test_ingest_document_calls_pipeline_run() -> None:
    mock_pipeline = AsyncMock()
    mock_build = MagicMock(return_value=mock_pipeline)
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()

    import ai.src.infrastructure.workers.tasks.indexing as tasks_module

    with (
        patch.object(tasks_module.asyncio, "run", side_effect=_fake_asyncio_run),
        patch("backend.src.infrastructure.database.session.engine", mock_engine),
        patch(
            "ai.src.application.indexing.dependencies.build_indexing_pipeline",
            mock_build,
        ),
    ):
        tasks_module.ingest_document.fn(str(_KB_ENTRY_ID))

    mock_build.assert_called_once()
    mock_pipeline.run.assert_awaited_once_with(str(_KB_ENTRY_ID))


def test_delete_document_calls_vector_store_delete() -> None:
    mock_store = AsyncMock()
    mock_engine = MagicMock()
    mock_engine.dispose = AsyncMock()

    import ai.src.infrastructure.workers.tasks.indexing as tasks_module

    with (
        patch.object(tasks_module.asyncio, "run", side_effect=_fake_asyncio_run),
        patch("backend.src.infrastructure.database.session.engine", mock_engine),
        patch(
            "ai.src.infrastructure.vector_store.pinecone.PineconeVectorStore",
            MagicMock(return_value=mock_store),
        ),
    ):
        tasks_module.delete_document.fn(str(_KB_ENTRY_ID))

    mock_store.delete_by_kb_entry.assert_awaited_once_with(_KB_ENTRY_ID)
