"""Unit tests: presentation/api/v1/dashboard/endpoints/get.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.dashboard.dependencies import get_get_department_dashboard
from backend.src.application.dashboard.results.get_department_dashboard import (
    GetDepartmentDashboardResult,
)
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_org_inviter


@pytest.mark.asyncio
async def test_get_department_dashboard_returns_200(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(), department_id=uuid4(), email="admin@example.com", role=UserRole.ADMIN
    )
    result = GetDepartmentDashboardResult(
        total_patients_seen=142,
        active_encounters=6,
        discharged_encounters=136,
        low_stock_items_count=2,
        average_visit_duration_minutes=47.5,
        esi_distribution={1: 1, 2: 8, 3: 40, 4: 70, 5: 17},
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_org_inviter] = lambda: auth
    app.dependency_overrides[get_get_department_dashboard] = lambda: mock_use_case
    try:
        response = await async_client.get(
            "/api/v1/dashboard/",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total_patients_seen"] == 142
    assert body["esi_distribution"] == {"1": 1, "2": 8, "3": 40, "4": 70, "5": 17}


@pytest.mark.asyncio
async def test_get_department_dashboard_rejects_unauthenticated(async_client) -> None:
    response = await async_client.get("/api/v1/dashboard/")

    assert response.status_code == 401
