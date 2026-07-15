"""Commands for patient check-in."""
from dataclasses import dataclass
from datetime import date
from uuid import UUID


@dataclass(frozen=True)
class CheckInPatientCommand:
    department_id: UUID
    patient_id: UUID | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    sex: str | None = None
    phone_number: str | None = None
    next_of_kin_name: str | None = None
    next_of_kin_phone: str | None = None
    insurance_status: str | None = None
