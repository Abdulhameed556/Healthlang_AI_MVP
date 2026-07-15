"""Unit tests: application/triage/use_cases/record_triage.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.triage.commands.record_triage import RecordTriageCommand
from backend.src.application.triage.use_cases.record_triage import RecordTriage
from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.triage.exceptions import TriageAlreadyRecordedError

_STABLE_VITALS = dict(
    bp_systolic=120,
    bp_diastolic=80,
    pulse=75,
    respiratory_rate=16,
    temperature=37.0,
)


def _encounter(status: EncounterStatus = EncounterStatus.CHECKED_IN) -> Encounter:
    now = datetime.now(timezone.utc)
    return Encounter(
        id=uuid4(),
        patient_id=uuid4(),
        department_id=uuid4(),
        status=status.value,
        checked_in_at=now,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture()
def triage_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.get_by_encounter_id = AsyncMock(return_value=None)
    repo.add = AsyncMock(side_effect=lambda record: record)
    return repo


@pytest.fixture()
def encounter_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda encounter: encounter)
    return repo


@pytest.fixture()
def unit_of_work() -> AsyncMock:
    uow = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture()
def use_case(triage_repository, encounter_repository, unit_of_work) -> RecordTriage:
    return RecordTriage(
        triage_repository=triage_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


@pytest.mark.asyncio
async def test_execute_accepts_suggested_level(
    use_case: RecordTriage, encounter_repository, unit_of_work
) -> None:
    encounter = _encounter()
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    result = await use_case.execute(
        RecordTriageCommand(
            encounter_id=encounter.id,
            recorded_by=uuid4(),
            **_STABLE_VITALS,
        )
    )

    assert result.esi_suggested_level == 3
    assert result.esi_level == 3
    assert result.was_overridden is False
    saved_encounter: Encounter = encounter_repository.save.await_args.args[0]
    assert saved_encounter.status == EncounterStatus.TRIAGED.value
    assert saved_encounter.esi_level == 3
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_applies_valid_override(
    use_case: RecordTriage, encounter_repository
) -> None:
    encounter = _encounter()
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    result = await use_case.execute(
        RecordTriageCommand(
            encounter_id=encounter.id,
            recorded_by=uuid4(),
            final_esi_level=4,
            override_reason="Ambulatory, minor complaint, no resources anticipated",
            **_STABLE_VITALS,
        )
    )

    assert result.esi_suggested_level == 3
    assert result.esi_level == 4
    assert result.was_overridden is True


@pytest.mark.asyncio
async def test_execute_rejects_override_without_reason(
    use_case: RecordTriage, encounter_repository
) -> None:
    encounter = _encounter()
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    with pytest.raises(ValidationError, match="reason is required"):
        await use_case.execute(
            RecordTriageCommand(
                encounter_id=encounter.id,
                recorded_by=uuid4(),
                final_esi_level=4,
                **_STABLE_VITALS,
            )
        )


@pytest.mark.asyncio
async def test_execute_raises_when_encounter_missing(
    use_case: RecordTriage, encounter_repository
) -> None:
    encounter_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(EncounterNotFoundError):
        await use_case.execute(
            RecordTriageCommand(
                encounter_id=uuid4(),
                recorded_by=uuid4(),
                **_STABLE_VITALS,
            )
        )


@pytest.mark.asyncio
async def test_execute_raises_when_already_triaged(
    use_case: RecordTriage, encounter_repository, triage_repository
) -> None:
    encounter = _encounter(status=EncounterStatus.TRIAGED)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)
    triage_repository.get_by_encounter_id = AsyncMock(return_value=object())

    with pytest.raises(TriageAlreadyRecordedError):
        await use_case.execute(
            RecordTriageCommand(
                encounter_id=encounter.id,
                recorded_by=uuid4(),
                **_STABLE_VITALS,
            )
        )


@pytest.mark.asyncio
async def test_execute_rejects_encounter_not_checked_in(
    use_case: RecordTriage, encounter_repository
) -> None:
    encounter = _encounter(status=EncounterStatus.IN_CONSULTATION)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    with pytest.raises(ValidationError, match="Cannot transition"):
        await use_case.execute(
            RecordTriageCommand(
                encounter_id=encounter.id,
                recorded_by=uuid4(),
                **_STABLE_VITALS,
            )
        )
