"""Unit tests: presentation API router."""
import pytest

from backend.src.presentation.api.v1.router import health


@pytest.mark.asyncio
async def test_health_returns_envelope() -> None:
    response = await health()

    assert response.error is False
    assert response.status_code == 200
    assert response.message == "OK"
    assert response.data is not None
    assert response.data.status == "ok"
