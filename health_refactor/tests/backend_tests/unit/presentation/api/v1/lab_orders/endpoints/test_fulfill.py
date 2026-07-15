"""Unit tests: presentation/api/v1/lab_orders/endpoints/fulfill.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.lab_orders.dependencies import get_fulfill_lab_order
from backend.src.application.lab_orders.results.fulfill_lab_order import (
    FulfillLabOrderResult,
)
from backend.src.domain.lab_orders.value_objects import LabOrderStatus
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_lab_scientist


@pytest.mark.asyncio
async def test_fulfill_lab_order_returns_200(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="lab@example.com",
        role=UserRole.LAB_SCIENTIST,
    )
    lab_order_id = uuid4()
    result = FulfillLabOrderResult(
        lab_order_id=lab_order_id,
        status=LabOrderStatus.COMPLETED.value,
        result_payload="Normal",
        fulfilled_at=datetime.now(timezone.utc),
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_lab_scientist] = lambda: auth
    app.dependency_overrides[get_fulfill_lab_order] = lambda: mock_use_case
    try:
        response = await async_client.post(
            f"/api/v1/lab-orders/{lab_order_id}/fulfill",
            headers={"Authorization": "Bearer test-access-token"},
            json={"result_payload": "Normal"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_fulfill_lab_order_rejects_non_lab_scientist(async_client) -> None:
    response = await async_client.post(
        f"/api/v1/lab-orders/{uuid4()}/fulfill",
        json={"result_payload": "x"},
    )

    assert response.status_code == 401
