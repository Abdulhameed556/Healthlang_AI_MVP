"""Unit tests: presentation/api/v1/encounters/endpoints/detail.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.dependencies import get_get_encounter
from backend.src.application.encounters.results.get_encounter import GetEncounterResult
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_auth


def _auth_context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="nurse@example.com",
        role=UserRole.NURSE,
    )


@pytest.mark.asyncio
async def test_get_encounter_returns_200(async_client) -> None:
    encounter_id = uuid4()
    result = GetEncounterResult(
        encounter_id=encounter_id,
        patient_id=uuid4(),
        department_id=uuid4(),
        status=EncounterStatus.TRIAGED.value,
        esi_level=2,
        checked_in_at=datetime.now(timezone.utc),
        closed_at=None,
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_auth] = lambda: _auth_context()
    app.dependency_overrides[get_get_encounter] = lambda: mock_use_case
    try:
        response = await async_client.get(
            f"/api/v1/encounters/{encounter_id}",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["status"] == "triaged"
    assert body["data"]["esi_level"] == 2


@pytest.mark.asyncio
async def test_get_encounter_requires_bearer(async_client) -> None:
    response = await async_client.get(f"/api/v1/encounters/{uuid4()}")

    assert response.status_code == 401
