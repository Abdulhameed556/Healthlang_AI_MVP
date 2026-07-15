"""Unit tests: presentation/api/v1/triage/endpoints/record.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.triage.dependencies import get_record_triage
from backend.src.application.triage.results.record_triage import RecordTriageResult
from backend.src.core.exceptions import ValidationError
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_nurse


def _auth_context(role: UserRole = UserRole.NURSE) -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="nurse@example.com",
        role=role,
    )


_VITALS = {
    "bp_systolic": 120,
    "bp_diastolic": 80,
    "pulse": 75,
    "respiratory_rate": 16,
    "temperature": 37.0,
}


@pytest.mark.asyncio
async def test_record_triage_returns_201(async_client) -> None:
    auth = _auth_context()
    encounter_id = uuid4()
    result = RecordTriageResult(
        triage_record_id=uuid4(),
        encounter_id=encounter_id,
        esi_suggested_level=3,
        esi_level=3,
        was_overridden=False,
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_nurse] = lambda: auth
    app.dependency_overrides[get_record_triage] = lambda: mock_use_case
    try:
        response = await async_client.post(
            f"/api/v1/triage/{encounter_id}",
            headers={"Authorization": "Bearer test-access-token"},
            json=_VITALS,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["data"]["esi_level"] == 3
    assert body["data"]["was_overridden"] is False


@pytest.mark.asyncio
async def test_record_triage_propagates_override_validation_error(async_client) -> None:
    auth = _auth_context()
    encounter_id = uuid4()
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(
        side_effect=ValidationError(
            "An override reason is required when changing the suggested ESI level"
        )
    )

    app.dependency_overrides[require_nurse] = lambda: auth
    app.dependency_overrides[get_record_triage] = lambda: mock_use_case
    try:
        response = await async_client.post(
            f"/api/v1/triage/{encounter_id}",
            headers={"Authorization": "Bearer test-access-token"},
            json={**_VITALS, "final_esi_level": 5},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422
    assert "reason is required" in response.json()["message"]


@pytest.mark.asyncio
async def test_record_triage_rejects_non_nurse(async_client) -> None:
    response = await async_client.post(
        f"/api/v1/triage/{uuid4()}",
        json=_VITALS,
    )

    assert response.status_code == 401
