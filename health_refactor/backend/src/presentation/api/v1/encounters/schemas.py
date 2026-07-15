"""Pydantic request/response schemas for encounters."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.src.domain.patients.value_objects import InsuranceStatus, Sex


class CheckInPatientRequest(BaseModel):
    patient_id: UUID | None = Field(
        default=None,
        description="Existing patient's UUID. Omit when registering a new patient.",
    )
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None
    sex: Sex | None = None
    phone_number: str | None = Field(default=None, max_length=30)
    next_of_kin_name: str | None = Field(default=None, max_length=200)
    next_of_kin_phone: str | None = Field(default=None, max_length=30)
    insurance_status: InsuranceStatus = InsuranceStatus.NONE

    @model_validator(mode="after")
    def validate_patient_or_demographics(self) -> "CheckInPatientRequest":
        new_patient_fields = (
            self.first_name,
            self.last_name,
            self.date_of_birth,
            self.sex,
            self.phone_number,
        )
        if self.patient_id is None and not all(new_patient_fields):
            raise ValueError(
                "Provide patient_id for a returning patient, or first_name, "
                "last_name, date_of_birth, sex, and phone_number for a new one"
            )
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "Ada",
                "last_name": "Lovelace",
                "date_of_birth": "1990-05-14",
                "sex": "female",
                "phone_number": "+2348012345678",
                "insurance_status": "none",
            }
        }
    )


class CheckInPatientResponse(BaseModel):
    encounter_id: UUID
    patient_id: UUID
    department_id: UUID
    status: str
    checked_in_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EncounterResponse(BaseModel):
    encounter_id: UUID
    patient_id: UUID
    department_id: UUID
    status: str
    esi_level: int | None = None
    checked_in_at: datetime
    closed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class QueueEntryResponse(BaseModel):
    encounter_id: UUID
    patient_id: UUID
    status: str
    esi_level: int | None = None
    checked_in_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QueueResponse(BaseModel):
    entries: list[QueueEntryResponse]

    model_config = ConfigDict(from_attributes=True)


class MarkOrdersFulfilledResponse(BaseModel):
    encounter_id: UUID
    status: str

    model_config = ConfigDict(from_attributes=True)


class DischargeEncounterResponse(BaseModel):
    encounter_id: UUID
    status: str
    closed_at: datetime

    model_config = ConfigDict(from_attributes=True)
