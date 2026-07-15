"""FastAPI dependency-injection providers for patients use-cases."""
from fastapi import Depends

from backend.src.application.patients.use_cases.get_patient import GetPatient
from backend.src.domain.patients.repositories import IPatientRepository
from backend.src.infrastructure.database.dependencies import get_patient_repository


def get_get_patient(
    patient_repository: IPatientRepository = Depends(get_patient_repository),
) -> GetPatient:
    return GetPatient(patient_repository=patient_repository)
