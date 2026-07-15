"""Unit tests: ai/src/application/indexing/ — steps and pipeline orchestrator."""
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

_KB_ENTRY_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_KB_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_ORG_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
_AGENT_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")


def _make_ctx(**overrides):
    from ai.src.application.indexing.context import IndexingContext

    defaults = dict(
        kb_entry_id=_KB_ENTRY_ID,
        knowledge_base_id=_KB_ID,
        organization_id=_ORG_ID,
        agent_ids=[_AGENT_ID],
        storage_path="orgs/org-1/entries/file.txt",
        file_type="txt",
    )
    return IndexingContext(**{**defaults, **overrides})


# ── FetchDocumentStep ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fetch_document_calls_s3_download(monkeypatch) -> None:
    import ai.src.application.indexing.steps.fetch_document as mod

    mock_download = AsyncMock(return_value=b"raw content")
    monkeypatch.setattr(mod, "download_file", mock_download)

    ctx = _make_ctx()
    await mod.FetchDocumentStep().run(ctx)

    mock_download.assert_called_once_with(ctx.storage_path)


@pytest.mark.asyncio
async def test_fetch_document_sets_raw_bytes_on_context(monkeypatch) -> None:
    import ai.src.application.indexing.steps.fetch_document as mod

    monkeypatch.setattr(mod, "download_file", AsyncMock(return_value=b"bytes"))

    ctx = _make_ctx()
    await mod.FetchDocumentStep().run(ctx)

    assert ctx.raw_bytes == b"bytes"


# ── ParseDocumentStep ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_parse_document_calls_correct_parser() -> None:
    from ai.src.application.indexing.steps.parse_document import ParseDocumentStep

    mock_parser = MagicMock()
    mock_parser.parse.return_value = "parsed text"
    mock_factory = MagicMock()
    mock_factory.get_parser.return_value = mock_parser

    ctx = _make_ctx(raw_bytes=b"raw", file_type="txt")
    await ParseDocumentStep(mock_factory).run(ctx)

    mock_factory.get_parser.assert_called_once_with("txt")
    mock_parser.parse.assert_called_once_with(b"raw", "txt")


@pytest.mark.asyncio
async def test_parse_document_sets_text_on_context() -> None:
    from ai.src.application.indexing.steps.parse_document import ParseDocumentStep

    mock_parser = MagicMock()
    mock_parser.parse.return_value = "clean text"
    mock_factory = MagicMock()
    mock_factory.get_parser.return_value = mock_parser

    ctx = _make_ctx(raw_bytes=b"raw", file_type="txt")
    await ParseDocumentStep(mock_factory).run(ctx)

    assert ctx.text == "clean text"


# ── ChunkTextStep ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_chunk_text_calls_chunker() -> None:
    from ai.src.application.indexing.steps.chunk_text import ChunkTextStep

    mock_chunker = MagicMock()
    mock_chunker.chunk.return_value = ["chunk a", "chunk b"]

    ctx = _make_ctx(text="some long text")
    await ChunkTextStep(mock_chunker).run(ctx)

    mock_chunker.chunk.assert_called_once_with("some long text", 500, 50)


@pytest.mark.asyncio
async def test_chunk_text_sets_chunk_texts_on_context() -> None:
    from ai.src.application.indexing.steps.chunk_text import ChunkTextStep

    mock_chunker = MagicMock()
    mock_chunker.chunk.return_value = ["chunk a", "chunk b"]

    ctx = _make_ctx(text="some long text")
    await ChunkTextStep(mock_chunker).run(ctx)

    assert ctx.chunk_texts == ["chunk a", "chunk b"]


# ── EmbedChunksStep ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_embed_chunks_calls_embedder() -> None:
    from ai.src.application.indexing.steps.embed_chunks import EmbedChunksStep

    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]

    ctx = _make_ctx(chunk_texts=["chunk a", "chunk b"])
    await EmbedChunksStep(mock_embedder).run(ctx)

    mock_embedder.embed.assert_called_once_with(["chunk a", "chunk b"])


@pytest.mark.asyncio
async def test_embed_chunks_sets_embeddings_on_context() -> None:
    from ai.src.application.indexing.steps.embed_chunks import EmbedChunksStep

    mock_embedder = AsyncMock()
    mock_embedder.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]

    ctx = _make_ctx(chunk_texts=["chunk a", "chunk b"])
    await EmbedChunksStep(mock_embedder).run(ctx)

    assert ctx.embeddings == [[0.1, 0.2], [0.3, 0.4]]


# ── UpsertVectorsStep ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_vectors_calls_vector_store() -> None:
    from ai.src.application.indexing.steps.upsert_vectors import UpsertVectorsStep

    mock_store = AsyncMock()
    ctx = _make_ctx(
        chunk_texts=["chunk a"],
        embeddings=[[0.1, 0.2]],
        agent_ids=[_AGENT_ID],
    )
    await UpsertVectorsStep(mock_store).run(ctx)

    mock_store.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_vectors_skips_when_no_agents() -> None:
    from ai.src.application.indexing.steps.upsert_vectors import UpsertVectorsStep

    mock_store = AsyncMock()
    ctx = _make_ctx(chunk_texts=["chunk a"], embeddings=[[0.1]], agent_ids=[])
    await UpsertVectorsStep(mock_store).run(ctx)

    mock_store.upsert.assert_not_called()


@pytest.mark.asyncio
async def test_upsert_vectors_creates_chunk_per_agent() -> None:
    from ai.src.application.indexing.steps.upsert_vectors import UpsertVectorsStep

    agent_a = UUID("11111111-1111-1111-1111-111111111111")
    agent_b = UUID("22222222-2222-2222-2222-222222222222")
    mock_store = AsyncMock()
    ctx = _make_ctx(
        chunk_texts=["chunk a"],
        embeddings=[[0.1, 0.2]],
        agent_ids=[agent_a, agent_b],
    )
    await UpsertVectorsStep(mock_store).run(ctx)

    chunks = mock_store.upsert.call_args[0][0]
    assert len(chunks) == 2
    agent_ids_in_chunks = {c.agent_id for c in chunks}
    assert agent_ids_in_chunks == {agent_a, agent_b}


# ── NotifyBackendStep ─────────────────────────────────────────────────────────


def _make_session_factory(mock_session: AsyncMock) -> MagicMock:
    ctx_mgr = AsyncMock(
        __aenter__=AsyncMock(return_value=mock_session),
        __aexit__=AsyncMock(),
    )
    return MagicMock(return_value=ctx_mgr)


@pytest.mark.asyncio
async def test_notify_backend_sets_status_indexed_on_success() -> None:
    from ai.src.application.indexing.steps.notify_backend import NotifyBackendStep

    mock_entry = MagicMock()
    mock_session = AsyncMock()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_entry)
    )

    ctx = _make_ctx(failed=False)
    await NotifyBackendStep(_make_session_factory(mock_session)).run(ctx)

    assert mock_entry.indexing_status == "indexed"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_notify_backend_sets_status_failed_on_error() -> None:
    from ai.src.application.indexing.steps.notify_backend import NotifyBackendStep

    mock_entry = MagicMock()
    mock_session = AsyncMock()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_entry)
    )

    ctx = _make_ctx(failed=True, error="S3 timeout")
    await NotifyBackendStep(_make_session_factory(mock_session)).run(ctx)

    assert mock_entry.indexing_status == "failed"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_notify_backend_skips_commit_when_entry_missing() -> None:
    from ai.src.application.indexing.steps.notify_backend import NotifyBackendStep

    mock_session = AsyncMock()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    ctx = _make_ctx()
    await NotifyBackendStep(_make_session_factory(mock_session)).run(ctx)

    mock_session.commit.assert_not_called()


# ── IndexingPipeline ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_runs_all_steps_and_notifies() -> None:
    from ai.src.application.indexing.pipeline import IndexingPipeline

    step_a = AsyncMock()
    step_b = AsyncMock()
    notify = AsyncMock()

    pipeline = IndexingPipeline.__new__(IndexingPipeline)
    pipeline._steps = [step_a, step_b]
    pipeline._notify_step = notify

    ctx = _make_ctx()
    pipeline._load_context = AsyncMock(return_value=ctx)

    await pipeline.run(str(_KB_ENTRY_ID))

    step_a.run.assert_called_once_with(ctx)
    step_b.run.assert_called_once_with(ctx)
    notify.run.assert_called_once_with(ctx)


@pytest.mark.asyncio
async def test_pipeline_marks_failed_and_notifies_on_step_error() -> None:
    from ai.src.application.indexing.pipeline import IndexingPipeline

    failing_step = AsyncMock()
    failing_step.run.side_effect = RuntimeError("S3 error")
    notify = AsyncMock()

    pipeline = IndexingPipeline.__new__(IndexingPipeline)
    pipeline._steps = [failing_step]
    pipeline._notify_step = notify

    ctx = _make_ctx()
    pipeline._load_context = AsyncMock(return_value=ctx)

    await pipeline.run(str(_KB_ENTRY_ID))

    assert ctx.failed is True
    assert "S3 error" in ctx.error
    notify.run.assert_called_once_with(ctx)


def test_pipeline_init_creates_all_steps() -> None:
    from ai.src.application.indexing.pipeline import IndexingPipeline
    from ai.src.application.indexing.steps.chunk_text import ChunkTextStep
    from ai.src.application.indexing.steps.embed_chunks import EmbedChunksStep
    from ai.src.application.indexing.steps.fetch_document import FetchDocumentStep
    from ai.src.application.indexing.steps.notify_backend import NotifyBackendStep
    from ai.src.application.indexing.steps.parse_document import ParseDocumentStep
    from ai.src.application.indexing.steps.upsert_vectors import UpsertVectorsStep

    pipeline = IndexingPipeline(
        session_factory=MagicMock(),
        embedder=MagicMock(),
        vector_store=MagicMock(),
        parser_factory=MagicMock(),
        chunker=MagicMock(),
    )

    step_types = [type(s) for s in pipeline._steps]
    assert FetchDocumentStep in step_types
    assert ParseDocumentStep in step_types
    assert ChunkTextStep in step_types
    assert EmbedChunksStep in step_types
    assert UpsertVectorsStep in step_types
    assert isinstance(pipeline._notify_step, NotifyBackendStep)


@pytest.mark.asyncio
async def test_pipeline_load_context_builds_indexing_context() -> None:
    from ai.src.application.indexing.pipeline import IndexingPipeline

    mock_entry = MagicMock()
    mock_entry.id = _KB_ENTRY_ID
    mock_entry.knowledge_base_id = _KB_ID
    mock_entry.storage_path = "orgs/o/f.txt"
    mock_entry.file_type = "txt"

    mock_kb = MagicMock()
    mock_kb.organization_id = _ORG_ID

    mock_agent_row = MagicMock()
    mock_agent_row.agent_id = _AGENT_ID

    scalars_mock = MagicMock(all=MagicMock(return_value=[mock_agent_row]))
    mock_session = AsyncMock()
    mock_session.execute.side_effect = [
        MagicMock(scalar_one=MagicMock(return_value=mock_entry)),
        MagicMock(scalar_one=MagicMock(return_value=mock_kb)),
        MagicMock(scalars=MagicMock(return_value=scalars_mock)),
    ]

    pipeline = IndexingPipeline.__new__(IndexingPipeline)
    pipeline._session_factory = _make_session_factory(mock_session)

    ctx = await pipeline._load_context(_KB_ENTRY_ID)

    assert ctx.kb_entry_id == _KB_ENTRY_ID
    assert ctx.knowledge_base_id == _KB_ID
    assert ctx.organization_id == _ORG_ID
    assert ctx.agent_ids == [_AGENT_ID]
    assert ctx.storage_path == "orgs/o/f.txt"
    assert ctx.file_type == "txt"
