"""Commands for patient lookup."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetPatientCommand:
    patient_id: UUID
