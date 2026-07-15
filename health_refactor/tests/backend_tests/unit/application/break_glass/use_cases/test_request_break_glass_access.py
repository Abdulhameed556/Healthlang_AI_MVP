"""Unit tests: application/break_glass/use_cases/request_break_glass_access.py"""
from datetime import date, datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.break_glass.commands.request_break_glass_access import (
    RequestBreakGlassAccessCommand,
)
from backend.src.application.break_glass.use_cases.request_break_glass_access import (
    RequestBreakGlassAccess,
)
from backend.src.domain.patients.entities import Patient
from backend.src.domain.patients.exceptions import PatientNotFoundError


def _patient() -> Patient:
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


@pytest.fixture()
def break_glass_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda r: r)
    return repo


@pytest.fixture()
def patient_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def audit_log_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda log: log)
    return repo


@pytest.fixture()
def unit_of_work() -> AsyncMock:
    uow = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture()
def use_case(
    break_glass_repository, patient_repository, audit_log_repository, unit_of_work
) -> RequestBreakGlassAccess:
    return RequestBreakGlassAccess(
        break_glass_repository=break_glass_repository,
        patient_repository=patient_repository,
        audit_log_repository=audit_log_repository,
        unit_of_work=unit_of_work,
    )


@pytest.mark.asyncio
async def test_execute_creates_request_and_audit_twin(
    use_case: RequestBreakGlassAccess,
    patient_repository,
    audit_log_repository,
    unit_of_work,
) -> None:
    patient = _patient()
    patient_repository.get_by_id = AsyncMock(return_value=patient)

    result = await use_case.execute(
        RequestBreakGlassAccessCommand(
            requesting_user_id=uuid4(),
            requesting_user_role="doctor",
            target_patient_id=patient.id,
            reason="Covering for Dr. Musa during a code blue",
        )
    )

    assert result.needs_review is True
    assert result.target_patient_id == patient.id
    audit_log_repository.add.assert_awaited_once()
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_raises_when_patient_missing(
    use_case: RequestBreakGlassAccess, patient_repository
) -> None:
    patient_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(PatientNotFoundError):
        await use_case.execute(
            RequestBreakGlassAccessCommand(
                requesting_user_id=uuid4(),
                requesting_user_role="doctor",
                target_patient_id=uuid4(),
                reason="x",
            )
        )
