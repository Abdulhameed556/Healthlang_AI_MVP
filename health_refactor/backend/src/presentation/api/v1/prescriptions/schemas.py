"""Pydantic request/response schemas for prescriptions."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreatePrescriptionRequest(BaseModel):
    inventory_item_id: UUID
    dosage: str = Field(..., min_length=1, max_length=200)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "inventory_item_id": "550e8400-e29b-41d4-a716-446655440000",
                "dosage": "500mg twice daily for 3 days",
            }
        }
    )


class CreatePrescriptionResponse(BaseModel):
    prescription_id: UUID
    encounter_id: UUID
    inventory_item_id: UUID
    dosage: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class DispensePrescriptionResponse(BaseModel):
    prescription_id: UUID
    status: str
    dispensed_at: datetime
    remaining_stock: int

    model_config = ConfigDict(from_attributes=True)


class PrescriptionSummaryResponse(BaseModel):
    prescription_id: UUID
    inventory_item_id: UUID
    dosage: str
    status: str
    created_at: datetime
    dispensed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ListPrescriptionsResponse(BaseModel):
    prescriptions: list[PrescriptionSummaryResponse]

    model_config = ConfigDict(from_attributes=True)
