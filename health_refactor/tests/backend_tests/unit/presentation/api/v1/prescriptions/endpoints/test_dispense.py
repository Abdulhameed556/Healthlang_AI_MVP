"""Unit tests: presentation/api/v1/prescriptions/endpoints/dispense.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.prescriptions.dependencies import get_dispense_prescription
from backend.src.application.prescriptions.results.dispense_prescription import (
    DispensePrescriptionResult,
)
from backend.src.domain.prescriptions.value_objects import PrescriptionStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_pharmacist


@pytest.mark.asyncio
async def test_dispense_prescription_returns_200(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="pharmacist@example.com",
        role=UserRole.PHARMACIST,
    )
    prescription_id = uuid4()
    result = DispensePrescriptionResult(
        prescription_id=prescription_id,
        status=PrescriptionStatus.DISPENSED.value,
        dispensed_at=datetime.now(timezone.utc),
        remaining_stock=9,
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_pharmacist] = lambda: auth
    app.dependency_overrides[get_dispense_prescription] = lambda: mock_use_case
    try:
        response = await async_client.post(
            f"/api/v1/prescriptions/{prescription_id}/dispense",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["remaining_stock"] == 9


@pytest.mark.asyncio
async def test_dispense_prescription_rejects_non_pharmacist(async_client) -> None:
    response = await async_client.post(f"/api/v1/prescriptions/{uuid4()}/dispense")

    assert response.status_code == 401
