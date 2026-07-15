"""Unit tests: domain/inventory/rules.py"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.src.domain.inventory.entities import InventoryItem
from backend.src.domain.inventory.exceptions import InsufficientStockError
from backend.src.domain.inventory.rules import assert_sufficient_stock


def _item(quantity_on_hand: int) -> InventoryItem:
    now = datetime.now(timezone.utc)
    return InventoryItem(
        id=uuid4(),
        department_id=uuid4(),
        drug_name="Paracetamol 500mg",
        quantity_on_hand=quantity_on_hand,
        reorder_threshold=10,
        created_at=now,
        updated_at=now,
    )


def test_assert_sufficient_stock_allows_exact_match() -> None:
    assert_sufficient_stock(_item(1), 1)


def test_assert_sufficient_stock_allows_surplus() -> None:
    assert_sufficient_stock(_item(50), 1)


def test_assert_sufficient_stock_rejects_zero_stock() -> None:
    with pytest.raises(InsufficientStockError, match="Insufficient stock"):
        assert_sufficient_stock(_item(0), 1)


def test_assert_sufficient_stock_rejects_below_requested() -> None:
    with pytest.raises(InsufficientStockError, match="Insufficient stock"):
        assert_sufficient_stock(_item(2), 5)
