"""Unit tests: application/encounters/use_cases/check_in_patient.py"""
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.encounters.commands.check_in_patient import (
    CheckInPatientCommand,
)
from backend.src.application.encounters.use_cases.check_in_patient import CheckInPatient
from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.patients.entities import Patient
from backend.src.domain.patients.exceptions import PatientNotFoundError


@pytest.fixture()
def patient_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda patient: patient)
    return repo


@pytest.fixture()
def encounter_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda encounter: encounter)
    return repo


@pytest.fixture()
def unit_of_work() -> AsyncMock:
    uow = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture()
def use_case(patient_repository, encounter_repository, unit_of_work) -> CheckInPatient:
    return CheckInPatient(
        patient_repository=patient_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


def _existing_patient() -> Patient:
    now = datetime.now(timezone.utc)
    return Patient(
        id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        date_of_birth=date(1990, 5, 14),
        sex="female",
        phone_number="+2348012345678",
        insurance_status="none",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_execute_checks_in_new_patient(
    use_case: CheckInPatient, patient_repository, encounter_repository, unit_of_work
) -> None:
    dept_id = uuid4()

    result = await use_case.execute(
        CheckInPatientCommand(
            department_id=dept_id,
            first_name="Ada",
            last_name="Lovelace",
            date_of_birth=date(1990, 5, 14),
            sex="female",
            phone_number="+2348012345678",
        )
    )

    patient_repository.add.assert_awaited_once()
    encounter_repository.add.assert_awaited_once()
    unit_of_work.commit.assert_awaited_once()
    assert result.department_id == dept_id
    assert result.status == EncounterStatus.CHECKED_IN.value


@pytest.mark.asyncio
async def test_execute_checks_in_returning_patient(
    use_case: CheckInPatient, patient_repository, encounter_repository
) -> None:
    existing = _existing_patient()
    patient_repository.get_by_id = AsyncMock(return_value=existing)
    dept_id = uuid4()

    result = await use_case.execute(
        CheckInPatientCommand(department_id=dept_id, patient_id=existing.id)
    )

    patient_repository.add.assert_not_awaited()
    encounter_repository.add.assert_awaited_once()
    assert result.patient_id == existing.id


@pytest.mark.asyncio
async def test_execute_raises_when_returning_patient_not_found(
    use_case: CheckInPatient, patient_repository
) -> None:
    patient_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(PatientNotFoundError):
        await use_case.execute(
            CheckInPatientCommand(department_id=uuid4(), patient_id=uuid4())
        )


@pytest.mark.asyncio
async def test_execute_raises_when_new_patient_missing_fields(use_case: CheckInPatient) -> None:
    with pytest.raises(ValidationError, match="requires"):
        await use_case.execute(
            CheckInPatientCommand(department_id=uuid4(), first_name="Ada")
        )
