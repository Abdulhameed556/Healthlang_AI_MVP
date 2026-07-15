"""Pydantic request/response schemas for patients."""
from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PatientResponse(BaseModel):
    patient_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    insurance_status: str
    next_of_kin_name: str | None = None
    next_of_kin_phone: str | None = None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "patient_id": "550e8400-e29b-41d4-a716-446655440000",
                "first_name": "Ada",
                "last_name": "Lovelace",
                "date_of_birth": "1990-05-14",
                "sex": "female",
                "phone_number": "+2348012345678",
                "insurance_status": "none",
                "next_of_kin_name": "Grace Hopper",
                "next_of_kin_phone": "+2348098765432",
            }
        },
    )
