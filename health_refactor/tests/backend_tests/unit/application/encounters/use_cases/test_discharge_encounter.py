"""Unit tests: application/encounters/use_cases/discharge_encounter.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.encounters.commands.discharge_encounter import (
    DischargeEncounterCommand,
)
from backend.src.application.encounters.use_cases.discharge_encounter import (
    DischargeEncounter,
)
from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.value_objects import EncounterStatus


def _encounter(status: EncounterStatus) -> Encounter:
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


@pytest.mark.asyncio
async def test_execute_discharges_directly_from_in_consultation() -> None:
    repo = AsyncMock()
    encounter = _encounter(EncounterStatus.IN_CONSULTATION)
    repo.get_by_id = AsyncMock(return_value=encounter)
    repo.save = AsyncMock(side_effect=lambda e: e)
    unit_of_work = AsyncMock()
    unit_of_work.commit = AsyncMock()
    use_case = DischargeEncounter(encounter_repository=repo, unit_of_work=unit_of_work)

    result = await use_case.execute(DischargeEncounterCommand(encounter_id=encounter.id))

    assert result.status == EncounterStatus.DISCHARGED.value
    assert result.closed_at is not None
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_discharges_from_fulfilled() -> None:
    repo = AsyncMock()
    encounter = _encounter(EncounterStatus.FULFILLED)
    repo.get_by_id = AsyncMock(return_value=encounter)
    repo.save = AsyncMock(side_effect=lambda e: e)
    use_case = DischargeEncounter(encounter_repository=repo, unit_of_work=AsyncMock())

    result = await use_case.execute(DischargeEncounterCommand(encounter_id=encounter.id))

    assert result.status == EncounterStatus.DISCHARGED.value


@pytest.mark.asyncio
async def test_execute_raises_when_encounter_missing() -> None:
    repo = AsyncMock()
    repo.get_by_id = AsyncMock(return_value=None)
    use_case = DischargeEncounter(encounter_repository=repo, unit_of_work=AsyncMock())

    with pytest.raises(EncounterNotFoundError):
        await use_case.execute(DischargeEncounterCommand(encounter_id=uuid4()))


@pytest.mark.asyncio
async def test_execute_rejects_discharge_with_orders_outstanding() -> None:
    repo = AsyncMock()
    encounter = _encounter(EncounterStatus.ORDER_PLACED)
    repo.get_by_id = AsyncMock(return_value=encounter)
    use_case = DischargeEncounter(encounter_repository=repo, unit_of_work=AsyncMock())

    with pytest.raises(ValidationError, match="Cannot transition"):
        await use_case.execute(DischargeEncounterCommand(encounter_id=encounter.id))
