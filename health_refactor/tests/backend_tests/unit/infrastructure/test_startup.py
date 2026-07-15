"""Unit tests: backend startup dependency checks."""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_verify_required_dependencies_checks_db_then_redis() -> None:
    from backend.src.infrastructure import startup as startup_mod

    order: list[str] = []

    async def _db() -> None:
        order.append("db")

    async def _redis() -> None:
        order.append("redis")

    with (
        patch.object(startup_mod, "verify_database_connection", side_effect=_db),
        patch.object(startup_mod, "verify_redis_connection", side_effect=_redis),
    ):
        await startup_mod.verify_required_dependencies()

    assert order == ["db", "redis"]


@pytest.mark.asyncio
async def test_verify_required_dependencies_stops_on_db_failure() -> None:
    from backend.src.infrastructure import startup as startup_mod

    verify_db = AsyncMock(side_effect=RuntimeError("db down"))
    verify_redis = AsyncMock()
    with (
        patch.object(startup_mod, "verify_database_connection", verify_db),
        patch.object(startup_mod, "verify_redis_connection", verify_redis),
    ):
        with pytest.raises(RuntimeError, match="db down"):
            await startup_mod.verify_required_dependencies()

    verify_redis.assert_not_awaited()


@pytest.mark.asyncio
async def test_verify_required_dependencies_stops_on_redis_failure() -> None:
    from backend.src.infrastructure import startup as startup_mod

    verify_db = AsyncMock()
    verify_redis = AsyncMock(side_effect=ConnectionError("redis down"))
    with (
        patch.object(startup_mod, "verify_database_connection", verify_db),
        patch.object(startup_mod, "verify_redis_connection", verify_redis),
    ):
        with pytest.raises(ConnectionError, match="redis down"):
            await startup_mod.verify_required_dependencies()

    verify_db.assert_awaited_once()
    verify_redis.assert_awaited_once()
