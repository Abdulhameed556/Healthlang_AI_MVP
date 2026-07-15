"""Unit tests: presentation/api/v1/inventory/endpoints/create.py"""
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.auth.context import AuthContext
from backend.src.application.inventory.dependencies import get_create_inventory_item
from backend.src.application.inventory.results.create_inventory_item import (
    CreateInventoryItemResult,
)
from backend.src.domain.users.value_objects import UserRole
from backend.src.main import app
from backend.src.presentation.dependencies.auth import require_pharmacist_or_admin


@pytest.mark.asyncio
async def test_create_inventory_item_returns_201(async_client) -> None:
    auth = AuthContext(
        user_id=uuid4(),
        department_id=uuid4(),
        email="pharmacist@example.com",
        role=UserRole.PHARMACIST,
    )
    result = CreateInventoryItemResult(
        item_id=uuid4(),
        department_id=auth.department_id,
        drug_name="Paracetamol 500mg",
        quantity_on_hand=100,
        reorder_threshold=20,
    )
    mock_use_case = AsyncMock()
    mock_use_case.execute = AsyncMock(return_value=result)

    app.dependency_overrides[require_pharmacist_or_admin] = lambda: auth
    app.dependency_overrides[get_create_inventory_item] = lambda: mock_use_case
    try:
        response = await async_client.post(
            "/api/v1/inventory/",
            headers={"Authorization": "Bearer test-access-token"},
            json={
                "drug_name": "Paracetamol 500mg",
                "quantity_on_hand": 100,
                "reorder_threshold": 20,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert response.json()["data"]["drug_name"] == "Paracetamol 500mg"


@pytest.mark.asyncio
async def test_create_inventory_item_rejects_non_pharmacist_or_admin(async_client) -> None:
    response = await async_client.post(
        "/api/v1/inventory/",
        json={"drug_name": "x", "quantity_on_hand": 1, "reorder_threshold": 1},
    )

    assert response.status_code == 401
