"""Unit tests: ai/src/infrastructure/llm/embedder.py — OpenAIEmbedder."""
from unittest.mock import MagicMock

import pytest


def _make_openai_client(embeddings: list[list[float]]) -> MagicMock:
    item_mocks = [MagicMock(embedding=e) for e in embeddings]
    client = MagicMock()
    client.embeddings.create.return_value = MagicMock(data=item_mocks)
    return client


@pytest.mark.asyncio
async def test_embed_calls_openai_create(monkeypatch) -> None:
    import ai.src.infrastructure.llm.embedder as embedder_module

    mock_client = _make_openai_client([[0.1, 0.2]])
    monkeypatch.setattr(
        embedder_module, "OpenAI", MagicMock(return_value=mock_client)
    )
    monkeypatch.setattr(embedder_module.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(
        embedder_module.settings, "default_embedding_model", "text-embedding-3-small"
    )

    embedder = embedder_module.OpenAIEmbedder()
    await embedder.embed(["hello world"])

    mock_client.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small", input=["hello world"]
    )


@pytest.mark.asyncio
async def test_embed_returns_embedding_vectors(monkeypatch) -> None:
    import ai.src.infrastructure.llm.embedder as embedder_module

    expected = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    mock_client = _make_openai_client(expected)
    monkeypatch.setattr(
        embedder_module, "OpenAI", MagicMock(return_value=mock_client)
    )
    monkeypatch.setattr(embedder_module.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(
        embedder_module.settings, "default_embedding_model", "text-embedding-3-small"
    )

    embedder = embedder_module.OpenAIEmbedder()
    result = await embedder.embed(["text one", "text two"])

    assert result == expected


def test_embed_sync_returns_list_of_embeddings() -> None:
    from ai.src.infrastructure.llm.embedder import _embed_sync

    expected = [[0.9, 0.8]]
    mock_client = _make_openai_client(expected)

    result = _embed_sync(mock_client, "text-embedding-3-small", ["hello"])

    assert result == expected
