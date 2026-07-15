"""Unit tests: presentation API router."""
import pytest

from ai.src.presentation.api.v1.router import health


@pytest.mark.asyncio
async def test_health_returns_ok() -> None:
    assert await health() == {"status": "ok"}
