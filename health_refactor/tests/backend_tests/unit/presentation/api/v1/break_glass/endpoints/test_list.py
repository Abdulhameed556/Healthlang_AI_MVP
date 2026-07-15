"""Unit tests: presentation/api/v1/break_glass/endpoints/list.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.break_glass.dependencies import get_list_break_glass_access
from backend.src.application.break_glass.results.list_break_glass_access import (
    BreakGlassAccessSummary,
    ListBreakGlassAccessResult,
)
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_super_admin


@pytest.mark.asyncio
async def test_list_break_glass_access_returns_200(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="superadmin@example.com",
        role=UserRole.SUPER_ADMIN,
    )
    result = ListBreakGlassAccessResult(
        requests=[
            BreakGlassAccessSummary(
                request_id=uuid4(),
                requesting_user_id=uuid4(),
                target_patient_id=uuid4(),
                reason="Emergency coverage",
                created_at=datetime.now(timezone.utc),
            )
        ]
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_super_admin] = lambda: auth
    app.dependency_overrides[get_list_break_glass_access] = lambda: mock_use_case
    try:
        response = await async_client.get(
            "/api/v1/break-glass/",
            headers={"Authorization": "Bearer test-access-token"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert len(response.json()["data"]["requests"]) == 1


@pytest.mark.asyncio
async def test_list_break_glass_access_rejects_unauthenticated(async_client) -> None:
    response = await async_client.get("/api/v1/break-glass/")

    assert response.status_code == 401
