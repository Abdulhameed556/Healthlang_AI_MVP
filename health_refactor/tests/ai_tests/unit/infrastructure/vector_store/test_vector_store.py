"""Unit tests: ai/src/infrastructure/vector_store/pinecone.py — PineconeVectorStore."""
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from ai.src.domain.knowledge_base.entities import DocumentChunk

_KB_ENTRY_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_AGENT_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
_ORG_ID = UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")

_CHUNK = DocumentChunk(
    chunk_id="chunk-1",
    kb_entry_id=_KB_ENTRY_ID,
    agent_id=_AGENT_ID,
    organization_id=_ORG_ID,
    text="The employee handbook covers leave policies.",
    embedding=[0.1, 0.2, 0.3],
)


def _make_index_mock() -> MagicMock:
    mock = MagicMock()
    mock.upsert = MagicMock()
    mock.query = MagicMock(return_value=MagicMock(matches=[]))
    mock.delete = MagicMock()
    return mock


# ── upsert ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upsert_calls_pinecone_upsert(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = _make_index_mock()
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    await pinecone_module.PineconeVectorStore().upsert([_CHUNK])

    mock_index.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_upsert_sends_correct_vector_id_and_values(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = _make_index_mock()
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    await pinecone_module.PineconeVectorStore().upsert([_CHUNK])

    vectors = mock_index.upsert.call_args.kwargs["vectors"]
    assert len(vectors) == 1
    v = vectors[0]
    assert v["id"] == "chunk-1"
    assert v["values"] == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_upsert_stores_required_metadata_fields(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = _make_index_mock()
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    await pinecone_module.PineconeVectorStore().upsert([_CHUNK])

    meta = mock_index.upsert.call_args.kwargs["vectors"][0]["metadata"]
    assert meta["kb_entry_id"] == str(_KB_ENTRY_ID)
    assert meta["agent_id"] == str(_AGENT_ID)
    assert meta["organization_id"] == str(_ORG_ID)
    assert meta["text"] == "The employee handbook covers leave policies."


# ── search ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_queries_with_agent_filter(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = _make_index_mock()
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    await pinecone_module.PineconeVectorStore().search([0.1, 0.2], _AGENT_ID, top_k=5)

    call_kwargs = mock_index.query.call_args.kwargs
    assert call_kwargs["top_k"] == 5
    assert call_kwargs["filter"] == {"agent_id": {"$eq": str(_AGENT_ID)}}
    assert call_kwargs["include_metadata"] is True


@pytest.mark.asyncio
async def test_search_returns_empty_list_when_no_matches(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = _make_index_mock()
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    result = await pinecone_module.PineconeVectorStore().search([0.1], _AGENT_ID, top_k=3)

    assert result == []


@pytest.mark.asyncio
async def test_search_maps_match_to_document_chunk(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    match = MagicMock()
    match.id = "chunk-1"
    match.values = [0.1, 0.2, 0.3]
    match.metadata = {
        "kb_entry_id": str(_KB_ENTRY_ID),
        "agent_id": str(_AGENT_ID),
        "organization_id": str(_ORG_ID),
        "text": "Leave policies",
    }
    mock_index = _make_index_mock()
    mock_index.query.return_value = MagicMock(matches=[match])
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    result = await pinecone_module.PineconeVectorStore().search([0.1, 0.2], _AGENT_ID, top_k=5)

    assert len(result) == 1
    chunk = result[0]
    assert chunk.chunk_id == "chunk-1"
    assert chunk.text == "Leave policies"
    assert chunk.kb_entry_id == _KB_ENTRY_ID
    assert chunk.agent_id == _AGENT_ID


# ── delete ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_delete_by_kb_entry_passes_correct_filter(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = _make_index_mock()
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    await pinecone_module.PineconeVectorStore().delete_by_kb_entry(_KB_ENTRY_ID)

    mock_index.delete.assert_called_once_with(
        filter={"kb_entry_id": {"$eq": str(_KB_ENTRY_ID)}}
    )


# ── kb_entry_id scoped search ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_search_adds_kb_entry_filter_when_provided(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = _make_index_mock()
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    await pinecone_module.PineconeVectorStore().search(
        [0.1, 0.2], _AGENT_ID, top_k=5, kb_entry_id=_KB_ENTRY_ID
    )

    call_filter = mock_index.query.call_args.kwargs["filter"]
    assert call_filter["agent_id"] == {"$eq": str(_AGENT_ID)}
    assert call_filter["kb_entry_id"] == {"$eq": str(_KB_ENTRY_ID)}


@pytest.mark.asyncio
async def test_search_omits_kb_entry_filter_when_none(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = _make_index_mock()
    monkeypatch.setattr(pinecone_module, "_get_index", lambda: mock_index)

    await pinecone_module.PineconeVectorStore().search(
        [0.1, 0.2], _AGENT_ID, top_k=5, kb_entry_id=None
    )

    call_filter = mock_index.query.call_args.kwargs["filter"]
    assert "kb_entry_id" not in call_filter


# ── _get_index ────────────────────────────────────────────────────────────────


def test_get_index_builds_pinecone_client(monkeypatch) -> None:
    import ai.src.infrastructure.vector_store.pinecone as pinecone_module

    mock_index = MagicMock()
    mock_pc = MagicMock()
    mock_pc.Index.return_value = mock_index
    mock_pinecone_cls = MagicMock(return_value=mock_pc)

    monkeypatch.setattr(pinecone_module.settings, "pinecone_api_key", "pc-test-key")
    monkeypatch.setattr(pinecone_module.settings, "pinecone_index_name", "test-index")

    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(__import__("sys").modules, "pinecone", MagicMock(Pinecone=mock_pinecone_cls))
        import sys
        sys.modules["pinecone"] = MagicMock(Pinecone=mock_pinecone_cls)
        result = pinecone_module._get_index()

    mock_pc.Index.assert_called_once_with("test-index")
    assert result is mock_index
