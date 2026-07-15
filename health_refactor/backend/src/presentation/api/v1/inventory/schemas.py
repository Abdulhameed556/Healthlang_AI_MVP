"""Pydantic request/response schemas for inventory."""
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateInventoryItemRequest(BaseModel):
    drug_name: str = Field(..., min_length=1, max_length=200)
    quantity_on_hand: int = Field(..., ge=0)
    reorder_threshold: int = Field(..., ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "drug_name": "Artemether/Lumefantrine 20/120mg",
                "quantity_on_hand": 200,
                "reorder_threshold": 30,
            }
        }
    )


class InventoryItemResponse(BaseModel):
    item_id: UUID
    department_id: UUID
    drug_name: str
    quantity_on_hand: int
    reorder_threshold: int

    model_config = ConfigDict(from_attributes=True)


class InventoryItemSummaryResponse(BaseModel):
    item_id: UUID
    drug_name: str
    quantity_on_hand: int
    reorder_threshold: int
    low_stock: bool

    model_config = ConfigDict(from_attributes=True)


class ListInventoryResponse(BaseModel):
    items: list[InventoryItemSummaryResponse]

    model_config = ConfigDict(from_attributes=True)
