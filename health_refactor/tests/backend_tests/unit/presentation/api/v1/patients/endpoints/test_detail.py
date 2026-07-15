"""Unit tests: presentation/api/v1/patients/endpoints/detail.py"""
from datetime import date
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.patients.dependencies import get_get_patient
from backend.src.application.patients.results.get_patient import GetPatientResult
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_auth


def _auth_context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="clerk@example.com",
        role=UserRole.FRONT_DESK,
    )


@pytest.mark.asyncio
async def test_get_patient_returns_200(async_client) -> None:
    patient_id = uuid4()
    result = GetPatientResult(
        patient_id=patient_id,
        first_name="Ada",
        last_name="Lovelace",
        date_of_birth=date(1990, 5, 14),
        sex="female",
        phone_number="+2348012345678",
        insurance_status="none",
        next_of_kin_name=None,
        next_of_kin_phone=None,
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_auth] = lambda: _auth_context()
    app.dependency_overrides[get_get_patient] = lambda: mock_use_case
    try:
        response = await async_client.get(
            f"/api/v1/patients/{patient_id}",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["first_name"] == "Ada"


@pytest.mark.asyncio
async def test_get_patient_requires_bearer(async_client) -> None:
    response = await async_client.get(f"/api/v1/patients/{uuid4()}")

    assert response.status_code == 401
