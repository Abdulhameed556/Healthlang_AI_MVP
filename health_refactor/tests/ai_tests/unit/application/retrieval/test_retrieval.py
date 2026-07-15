"""Unit tests: ai/src/application/retrieval/ — steps and pipeline."""
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

_AGENT_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_QUERY = "How do I reset my password?"
_EMBEDDING = [0.1, 0.2, 0.3]


def _make_ctx(**overrides):
    from ai.src.application.retrieval.context import RetrievalContext

    defaults = dict(query=_QUERY, agent_id=_AGENT_ID, top_k=5)
    return RetrievalContext(**{**defaults, **overrides})


# ── RetrievalContext ──────────────────────────────────────────────────────────


def test_retrieval_context_defaults() -> None:
    from ai.src.application.retrieval.context import RetrievalContext

    ctx = RetrievalContext(query=_QUERY, agent_id=_AGENT_ID)

    assert ctx.top_k == 5
    assert ctx.query_embedding == []
    assert ctx.chunks == []


# ── EmbedQueryStep ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_embed_query_calls_embedder() -> None:
    from ai.src.application.retrieval.steps.embed_query import EmbedQueryStep

    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = [_EMBEDDING]

    ctx = _make_ctx()
    await EmbedQueryStep(mock_embedder).run(ctx)

    mock_embedder.embed.assert_called_once_with([_QUERY])


@pytest.mark.asyncio
async def test_embed_query_sets_query_embedding() -> None:
    from ai.src.application.retrieval.steps.embed_query import EmbedQueryStep

    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = [_EMBEDDING]

    ctx = _make_ctx()
    await EmbedQueryStep(mock_embedder).run(ctx)

    assert ctx.query_embedding == _EMBEDDING


# ── SearchVectorStoreStep ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_vector_store_calls_store() -> None:
    from ai.src.application.retrieval.steps.search_vector_store import (
        SearchVectorStoreStep,
    )

    mock_store = AsyncMock()
    mock_store.search.return_value = []

    ctx = _make_ctx(query_embedding=_EMBEDDING, top_k=3)
    await SearchVectorStoreStep(mock_store).run(ctx)

    mock_store.search.assert_called_once_with(
        query_embedding=_EMBEDDING, agent_id=_AGENT_ID, top_k=3, kb_entry_id=None
    )


@pytest.mark.asyncio
async def test_search_vector_store_sets_chunks() -> None:
    from ai.src.application.retrieval.steps.search_vector_store import (
        SearchVectorStoreStep,
    )

    mock_chunk = MagicMock()
    mock_store = AsyncMock()
    mock_store.search.return_value = [mock_chunk]

    ctx = _make_ctx(query_embedding=_EMBEDDING)
    await SearchVectorStoreStep(mock_store).run(ctx)

    assert ctx.chunks == [mock_chunk]


# ── RetrievalPipeline ─────────────────────────────────────────────────────────


def test_retrieval_pipeline_init_creates_steps() -> None:
    from ai.src.application.retrieval.pipeline import RetrievalPipeline
    from ai.src.application.retrieval.steps.embed_query import EmbedQueryStep
    from ai.src.application.retrieval.steps.search_vector_store import (
        SearchVectorStoreStep,
    )

    pipeline = RetrievalPipeline(
        embedder=MagicMock(), vector_store=MagicMock()
    )

    step_types = [type(s) for s in pipeline._steps]
    assert EmbedQueryStep in step_types
    assert SearchVectorStoreStep in step_types


@pytest.mark.asyncio
async def test_retrieval_pipeline_retrieve_returns_chunks() -> None:
    from ai.src.application.retrieval.pipeline import RetrievalPipeline
    from ai.src.domain.knowledge_base.entities import DocumentChunk

    mock_chunk = MagicMock(spec=DocumentChunk)
    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = [_EMBEDDING]
    mock_store = AsyncMock()
    mock_store.search.return_value = [mock_chunk]

    pipeline = RetrievalPipeline(embedder=mock_embedder, vector_store=mock_store)
    result = await pipeline.retrieve(_QUERY, _AGENT_ID, top_k=5)

    assert result == [mock_chunk]


@pytest.mark.asyncio
async def test_retrieval_pipeline_retrieve_uses_default_top_k() -> None:
    from ai.src.application.retrieval.pipeline import RetrievalPipeline

    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = [_EMBEDDING]
    mock_store = AsyncMock()
    mock_store.search.return_value = []

    pipeline = RetrievalPipeline(embedder=mock_embedder, vector_store=mock_store)
    await pipeline.retrieve(_QUERY, _AGENT_ID)

    _, kwargs = mock_store.search.call_args
    assert kwargs["top_k"] == 5


@pytest.mark.asyncio
async def test_retrieval_pipeline_passes_agent_id_to_store() -> None:
    from ai.src.application.retrieval.pipeline import RetrievalPipeline

    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = [_EMBEDDING]
    mock_store = AsyncMock()
    mock_store.search.return_value = []

    pipeline = RetrievalPipeline(embedder=mock_embedder, vector_store=mock_store)
    await pipeline.retrieve(_QUERY, _AGENT_ID)

    _, kwargs = mock_store.search.call_args
    assert kwargs["agent_id"] == _AGENT_ID
