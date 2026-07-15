"""Unit tests: presentation/api/v1/encounters/endpoints/discharge.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.dependencies import get_discharge_encounter
from backend.src.application.encounters.results.discharge_encounter import (
    DischargeEncounterResult,
)
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_doctor


@pytest.mark.asyncio
async def test_discharge_encounter_returns_200(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(), department_id=uuid4(), email="doctor@example.com", role=UserRole.DOCTOR
    )
    encounter_id = uuid4()
    result = DischargeEncounterResult(
        encounter_id=encounter_id,
        status=EncounterStatus.DISCHARGED.value,
        closed_at=datetime.now(timezone.utc),
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_doctor] = lambda: auth
    app.dependency_overrides[get_discharge_encounter] = lambda: mock_use_case
    try:
        response = await async_client.post(
            f"/api/v1/encounters/{encounter_id}/discharge",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "discharged"


@pytest.mark.asyncio
async def test_discharge_encounter_rejects_non_doctor(async_client) -> None:
    response = await async_client.post(f"/api/v1/encounters/{uuid4()}/discharge")

    assert response.status_code == 401
