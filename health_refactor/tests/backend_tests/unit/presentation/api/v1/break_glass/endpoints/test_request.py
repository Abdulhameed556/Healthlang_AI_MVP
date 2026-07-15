"""Unit tests: presentation/api/v1/break_glass/endpoints/request.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.break_glass.dependencies import (
    get_request_break_glass_access,
)
from backend.src.application.break_glass.results.request_break_glass_access import (
    RequestBreakGlassAccessResult,
)
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_clinical_staff


@pytest.mark.asyncio
async def test_request_break_glass_access_returns_201(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(), department_id=uuid4(), email="doctor@example.com", role=UserRole.DOCTOR
    )
    patient_id = uuid4()
    result = RequestBreakGlassAccessResult(
        request_id=uuid4(),
        target_patient_id=patient_id,
        needs_review=True,
        created_at=datetime.now(timezone.utc),
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_clinical_staff] = lambda: auth
    app.dependency_overrides[get_request_break_glass_access] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/break-glass/",
            headers={"Authorization": "Bearer test-access-token"},
            json={
                "target_patient_id": str(patient_id),
                "reason": "Covering for Dr. Musa during a code blue",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["data"]["needs_review"] is True


@pytest.mark.asyncio
async def test_request_break_glass_access_rejects_non_clinical_staff(async_client) -> None:
    response = await async_client.post(
        "/api/v1/break-glass/",
        json={"target_patient_id": str(uuid4()), "reason": "x"},
    )

    assert response.status_code == 401
