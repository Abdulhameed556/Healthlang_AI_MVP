"""Abstract repository interface for patients."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.patients.entities import Patient


class IPatientRepository(Protocol):
    async def get_by_id(self, patient_id: UUID) -> Patient | None: ...
    async def add(self, patient: Patient) -> Patient: ...
    async def save(self, patient: Patient) -> Patient: ...
