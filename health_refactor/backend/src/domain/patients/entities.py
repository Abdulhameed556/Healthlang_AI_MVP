"""Domain entities for patients."""
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass
class Patient:
    id: UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    insurance_status: str
    created_at: datetime
    updated_at: datetime
    next_of_kin_name: str | None = None
    next_of_kin_phone: str | None = None
