"""Unit tests: presentation/api/v1/triage/endpoints/detail.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.triage.dependencies import get_get_triage_record
from backend.src.application.triage.results.get_triage_record import GetTriageRecordResult
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_auth


def _auth_context() -> AuthContext:
    return AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="doctor@example.com",
        role=UserRole.DOCTOR,
    )


@pytest.mark.asyncio
async def test_get_triage_record_returns_200(async_client) -> None:
    encounter_id = uuid4()
    result = GetTriageRecordResult(
        triage_record_id=uuid4(),
        encounter_id=encounter_id,
        recorded_by=uuid4(),
        bp_systolic=120,
        bp_diastolic=80,
        pulse=75,
        respiratory_rate=16,
        temperature=37.0,
        esi_suggested_level=3,
        esi_level=3,
        created_at=datetime.now(timezone.utc),
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_auth] = lambda: _auth_context()
    app.dependency_overrides[get_get_triage_record] = lambda: mock_use_case
    try:
        response = await async_client.get(
            f"/api/v1/triage/{encounter_id}",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["esi_level"] == 3


@pytest.mark.asyncio
async def test_get_triage_record_requires_bearer(async_client) -> None:
    response = await async_client.get(f"/api/v1/triage/{uuid4()}")

    assert response.status_code == 401
