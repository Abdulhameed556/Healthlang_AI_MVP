"""Unit tests: application/encounters/use_cases/get_encounter.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.encounters.commands.get_encounter import GetEncounterCommand
from backend.src.application.encounters.use_cases.get_encounter import GetEncounter
from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.value_objects import EncounterStatus


@pytest.fixture()
def encounter_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def use_case(encounter_repository: AsyncMock) -> GetEncounter:
    return GetEncounter(encounter_repository=encounter_repository)


@pytest.mark.asyncio
async def test_execute_returns_encounter(
    use_case: GetEncounter, encounter_repository: AsyncMock
) -> None:
    now = datetime.now(timezone.utc)
    encounter = Encounter(
        id=uuid4(),
        patient_id=uuid4(),
        department_id=uuid4(),
        status=EncounterStatus.TRIAGED.value,
        esi_level=3,
        checked_in_at=now,
        created_at=now,
        updated_at=now,
    )
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    result = await use_case.execute(GetEncounterCommand(encounter_id=encounter.id))

    assert result.encounter_id == encounter.id
    assert result.status == EncounterStatus.TRIAGED.value
    assert result.esi_level == 3


@pytest.mark.asyncio
async def test_execute_raises_when_missing(
    use_case: GetEncounter, encounter_repository: AsyncMock
) -> None:
    encounter_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(EncounterNotFoundError):
        await use_case.execute(GetEncounterCommand(encounter_id=uuid4()))
