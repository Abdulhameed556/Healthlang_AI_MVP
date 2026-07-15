"""Unit tests: presentation/api/v1/encounters/endpoints/check_in.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.encounters.dependencies import get_check_in_patient
from backend.src.application.encounters.results.check_in_patient import (
    CheckInPatientResult,
)
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_front_desk


def _auth_context(role: UserRole = UserRole.FRONT_DESK) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="clerk@example.com",
        role=role,
    )


@pytest.mark.asyncio
async def test_check_in_new_patient_returns_201(async_client) -> None:
    auth = _auth_context()
    result = CheckInPatientResult(
        encounter_id=uuid4(),
        patient_id=uuid4(),
        department_id=auth.department_id,
        status=EncounterStatus.CHECKED_IN.value,
        checked_in_at=datetime.now(timezone.utc),
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_front_desk] = lambda: auth
    app.dependency_overrides[get_check_in_patient] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/encounters/check-in",
            headers={"Authorization": "Bearer test-access-token"},
            json={
                "first_name": "Ada",
                "last_name": "Lovelace",
                "date_of_birth": "1990-05-14",
                "sex": "female",
                "phone_number": "+2348012345678",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["error"] is False
    assert body["data"]["status"] == "checked_in"
    mock_use_case.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_in_rejects_missing_demographics_and_patient_id(async_client) -> None:
    auth = _auth_context()
    app.dependency_overrides[require_front_desk] = lambda: auth
    try:
        response = await async_client.post(
            "/api/v1/encounters/check-in",
            headers={"Authorization": "Bearer test-access-token"},
            json={"first_name": "Ada"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_check_in_rejects_non_front_desk(async_client) -> None:
    response = await async_client.post(
        "/api/v1/encounters/check-in",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "date_of_birth": "1990-05-14",
            "sex": "female",
            "phone_number": "+2348012345678",
        },
    )

    assert response.status_code == 401
