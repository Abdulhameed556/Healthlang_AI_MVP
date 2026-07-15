"""Pydantic request/response schemas for break-glass access."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RequestBreakGlassAccessRequest(BaseModel):
    target_patient_id: UUID
    reason: str = Field(..., min_length=1, max_length=1000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "target_patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "reason": "Covering for Dr. Musa during a code blue; patient not on my roster.",
            }
        }
    )


class RequestBreakGlassAccessResponse(BaseModel):
    request_id: UUID
    target_patient_id: UUID
    needs_review: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BreakGlassAccessSummaryResponse(BaseModel):
    request_id: UUID
    requesting_user_id: UUID
    target_patient_id: UUID
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListBreakGlassAccessResponse(BaseModel):
    requests: list[BreakGlassAccessSummaryResponse]

    model_config = ConfigDict(from_attributes=True)


class ReviewBreakGlassAccessResponse(BaseModel):
    request_id: UUID
    needs_review: bool
    reviewed_by: UUID
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)
