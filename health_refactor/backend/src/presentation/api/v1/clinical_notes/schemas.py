"""Pydantic request/response schemas for clinical notes."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateClinicalNoteRequest(BaseModel):
    diagnosis: str = Field(..., min_length=1, max_length=2000)
    notes: str = Field(..., min_length=1, max_length=10000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "diagnosis": "Uncomplicated malaria",
                "notes": "Afebrile on exam, mild fatigue. Started on ACT, review in 3 days.",
            }
        }
    )


class ClinicalNoteResponse(BaseModel):
    note_id: UUID
    encounter_id: UUID
    diagnosis: str
    notes: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClinicalNoteSummaryResponse(BaseModel):
    note_id: UUID
    doctor_id: UUID
    diagnosis: str
    notes: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ListClinicalNotesResponse(BaseModel):
    notes: list[ClinicalNoteSummaryResponse]

    model_config = ConfigDict(from_attributes=True)
