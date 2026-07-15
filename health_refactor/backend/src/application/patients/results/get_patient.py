"""Results for patient lookup."""
from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class GetPatientResult:
    patient_id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    insurance_status: str
    next_of_kin_name: str | None
    next_of_kin_phone: str | None
