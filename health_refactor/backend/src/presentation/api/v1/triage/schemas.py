"""Pydantic request/response schemas for triage."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.src.domain.triage.esi_rules import MAX_ESI_LEVEL, MIN_ESI_LEVEL


class RecordTriageRequest(BaseModel):
    bp_systolic: int = Field(..., gt=0, lt=300)
    bp_diastolic: int = Field(..., gt=0, lt=200)
    pulse: int = Field(..., gt=0, lt=300)
    respiratory_rate: int = Field(..., gt=0, lt=100)
    temperature: float = Field(..., description="Degrees Celsius.")
    weight_kg: float | None = Field(default=None, gt=0)
    final_esi_level: int | None = Field(
        default=None,
        ge=MIN_ESI_LEVEL,
        le=MAX_ESI_LEVEL,
        description="Omit to accept the system-suggested level as-is.",
    )
    override_reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Required if final_esi_level differs from the suggested level.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "bp_systolic": 118,
                "bp_diastolic": 76,
                "pulse": 82,
                "respiratory_rate": 16,
                "temperature": 37.0,
                "weight_kg": 68.5,
            }
        }
    )


class RecordTriageResponse(BaseModel):
    triage_record_id: UUID
    encounter_id: UUID
    esi_suggested_level: int
    esi_level: int
    was_overridden: bool

    model_config = ConfigDict(from_attributes=True)


class TriageRecordResponse(BaseModel):
    triage_record_id: UUID
    encounter_id: UUID
    recorded_by: UUID
    bp_systolic: int
    bp_diastolic: int
    pulse: int
    respiratory_rate: int
    temperature: float
    weight_kg: float | None = None
    esi_suggested_level: int
    esi_level: int
    override_reason: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
