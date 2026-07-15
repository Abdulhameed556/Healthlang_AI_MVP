"""Unit tests: presentation/api/v1/lab_orders/endpoints/create.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.lab_orders.dependencies import get_create_lab_order
from backend.src.application.lab_orders.results.create_lab_order import CreateLabOrderResult
from backend.src.domain.lab_orders.value_objects import LabOrderStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_doctor


@pytest.mark.asyncio
async def test_create_lab_order_returns_201(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(), department_id=uuid4(), email="doctor@example.com", role=UserRole.DOCTOR
    )
    encounter_id = uuid4()
    result = CreateLabOrderResult(
        lab_order_id=uuid4(),
        encounter_id=encounter_id,
        test_type="Full blood count",
        status=LabOrderStatus.PENDING.value,
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_doctor] = lambda: auth
    app.dependency_overrides[get_create_lab_order] = lambda: mock_use_case
    try:
        response = await async_client.post(
            f"/api/v1/lab-orders/{encounter_id}",
            headers={"Authorization": "Bearer test-access-token"},
            json={"test_type": "Full blood count"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_create_lab_order_rejects_non_doctor(async_client) -> None:
    response = await async_client.post(
        f"/api/v1/lab-orders/{uuid4()}",
        json={"test_type": "x"},
    )

    assert response.status_code == 401
