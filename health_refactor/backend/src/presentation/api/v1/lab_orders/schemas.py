"""Pydantic request/response schemas for lab orders."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateLabOrderRequest(BaseModel):
    test_type: str = Field(..., min_length=1, max_length=200)

    model_config = ConfigDict(
        json_schema_extra={"example": {"test_type": "Full blood count"}}
    )


class CreateLabOrderResponse(BaseModel):
    lab_order_id: UUID
    encounter_id: UUID
    test_type: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class FulfillLabOrderRequest(BaseModel):
    result_payload: str = Field(..., min_length=1, max_length=10000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"result_payload": "WBC 7.2, Hb 13.5, Platelets 250 — within range"}
        }
    )


class FulfillLabOrderResponse(BaseModel):
    lab_order_id: UUID
    status: str
    result_payload: str
    fulfilled_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LabOrderSummaryResponse(BaseModel):
    lab_order_id: UUID
    test_type: str
    status: str
    result_payload: str | None = None
    created_at: datetime
    fulfilled_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class ListLabOrdersResponse(BaseModel):
    orders: list[LabOrderSummaryResponse]

    model_config = ConfigDict(from_attributes=True)
