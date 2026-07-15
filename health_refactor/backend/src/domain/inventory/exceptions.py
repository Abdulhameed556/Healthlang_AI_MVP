"""Domain exceptions for inventory."""
from backend.src.core.exceptions import ConflictError, NotFoundError


class InventoryItemNotFoundError(NotFoundError):
    """Raised when an inventory item id does not exist."""


class InsufficientStockError(ConflictError):
    """Raised when dispensing would take stock below zero."""
