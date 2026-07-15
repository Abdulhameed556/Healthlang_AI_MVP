"""Unit tests: application/patients/use_cases/get_patient.py"""
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.patients.commands.get_patient import GetPatientCommand
from backend.src.application.patients.use_cases.get_patient import GetPatient
from backend.src.domain.patients.entities import Patient
from backend.src.domain.patients.exceptions import PatientNotFoundError


@pytest.fixture()
def patient_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def use_case(patient_repository: AsyncMock) -> GetPatient:
    return GetPatient(patient_repository=patient_repository)


@pytest.mark.asyncio
async def test_execute_returns_patient(use_case: GetPatient, patient_repository: AsyncMock) -> None:
    now = datetime.now(timezone.utc)
    patient = Patient(
        id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        date_of_birth=date(1990, 5, 14),
        sex="female",
        phone_number="+2348012345678",
        insurance_status="none",
        next_of_kin_name="Grace Hopper",
        next_of_kin_phone="+2348098765432",
        created_at=now,
        updated_at=now,
    )
    patient_repository.get_by_id = AsyncMock(return_value=patient)

    result = await use_case.execute(GetPatientCommand(patient_id=patient.id))

    assert result.patient_id == patient.id
    assert result.first_name == "Ada"
    assert result.next_of_kin_name == "Grace Hopper"


@pytest.mark.asyncio
async def test_execute_raises_when_missing(
    use_case: GetPatient, patient_repository: AsyncMock
) -> None:
    patient_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(PatientNotFoundError):
        await use_case.execute(GetPatientCommand(patient_id=uuid4()))
