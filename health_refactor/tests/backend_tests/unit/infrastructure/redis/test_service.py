"""Unit tests: backend RedisService."""
from unittest.mock import AsyncMock

import pytest

from backend.src.infrastructure.redis.service import RedisService


@pytest.mark.asyncio
async def test_ping_returns_true_when_redis_responds() -> None:
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    service = RedisService(client)

    assert await service.ping() is True


@pytest.mark.asyncio
async def test_set_uses_setex_when_ttl_provided() -> None:
    client = AsyncMock()
    service = RedisService(client)

    await service.set("agent_runtime:v1:agent-1", "payload", ttl_seconds=3600)

    client.setex.assert_awaited_once_with("agent_runtime:v1:agent-1", 3600, "payload")
    client.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_set_uses_set_without_ttl() -> None:
    client = AsyncMock()
    service = RedisService(client)

    await service.set("agent_runtime:v1:agent-1", "payload")

    client.set.assert_awaited_once_with("agent_runtime:v1:agent-1", "payload")
    client.setex.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_json_round_trips_dict_payload() -> None:
    client = AsyncMock()
    client.get = AsyncMock(return_value='{"agent_id":"abc","version_number":2}')
    service = RedisService(client)

    data = await service.get_json("agent_runtime:v1:agent-1:version-1")

    assert data == {"agent_id": "abc", "version_number": 2}


@pytest.mark.asyncio
async def test_set_json_serializes_dict() -> None:
    client = AsyncMock()
    service = RedisService(client)

    await service.set_json(
        "agent_runtime:v1:agent-1:version-1",
        {"agent_id": "abc", "version_number": 2},
        ttl_seconds=60,
    )

    client.setex.assert_awaited_once()
    key, ttl, payload = client.setex.await_args.args
    assert key == "agent_runtime:v1:agent-1:version-1"
    assert ttl == 60
    assert '"agent_id": "abc"' in payload


@pytest.mark.asyncio
async def test_delete_returns_removed_key_count() -> None:
    client = AsyncMock()
    client.delete = AsyncMock(return_value=1)
    service = RedisService(client)

    removed = await service.delete("agent_runtime:v1:agent-1:version-1")

    assert removed == 1
    client.delete.assert_awaited_once_with("agent_runtime:v1:agent-1:version-1")


@pytest.mark.asyncio
async def test_delete_with_no_keys_is_noop() -> None:
    client = AsyncMock()
    service = RedisService(client)

    removed = await service.delete()

    assert removed == 0
    client.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_by_prefix_scans_and_deletes_matching_keys() -> None:
    client = AsyncMock()

    async def _scan_iter(*, match):
        for key in [
            "agent_runtime:v1:agent-1:version-1",
            "agent_runtime:v1:agent-1:version-2",
        ]:
            yield key

    client.scan_iter = _scan_iter
    client.delete = AsyncMock(return_value=1)
    service = RedisService(client)

    removed = await service.delete_by_prefix("agent_runtime:v1:agent-1:")

    assert removed == 2
    assert client.delete.await_count == 2
