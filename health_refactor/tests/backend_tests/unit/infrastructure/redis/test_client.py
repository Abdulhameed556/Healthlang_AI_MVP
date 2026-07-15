"""Unit tests: backend Redis client factory."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.src.infrastructure.redis import client as client_mod


@pytest.mark.asyncio
async def test_get_redis_is_singleton_then_close() -> None:
    mock_client = MagicMock()
    mock_client.aclose = AsyncMock()
    with patch(
        "backend.src.infrastructure.redis.client.redis.from_url",
        return_value=mock_client,
    ) as from_url:
        await client_mod.close_redis()
        first = client_mod.get_redis()
        second = client_mod.get_redis()

    assert first is second
    from_url.assert_called_once()
    await client_mod.close_redis()
    assert getattr(client_mod._local, "client", None) is None
    mock_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_redis_connection_pings() -> None:
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(return_value=True)
    with patch(
        "backend.src.infrastructure.redis.client.get_redis",
        return_value=mock_client,
    ):
        await client_mod.verify_redis_connection()
    mock_client.ping.assert_awaited_once()


@pytest.mark.asyncio
async def test_verify_redis_connection_propagates_errors() -> None:
    mock_client = MagicMock()
    mock_client.ping = AsyncMock(side_effect=ConnectionError("refused"))
    with patch(
        "backend.src.infrastructure.redis.client.get_redis",
        return_value=mock_client,
    ):
        with pytest.raises(ConnectionError, match="refused"):
            await client_mod.verify_redis_connection()


@pytest.mark.asyncio
async def test_close_when_already_closed_is_noop() -> None:
    await client_mod.close_redis()
    await client_mod.close_redis()
    assert getattr(client_mod._local, "client", None) is None
