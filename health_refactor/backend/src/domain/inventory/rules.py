"""Rules for decrementing inventory stock."""
from backend.src.domain.inventory.entities import InventoryItem
from backend.src.domain.inventory.exceptions import InsufficientStockError


def assert_sufficient_stock(item: InventoryItem, quantity: int) -> None:
    """Validate dispensing `quantity` units won't take stock below zero."""
    if item.quantity_on_hand < quantity:
        raise InsufficientStockError(
            f"Insufficient stock for '{item.drug_name}': "
            f"{item.quantity_on_hand} on hand, {quantity} requested"
        )
