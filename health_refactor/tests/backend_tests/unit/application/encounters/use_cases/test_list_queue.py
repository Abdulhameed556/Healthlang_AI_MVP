"""Unit tests: application/encounters/use_cases/list_queue.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.encounters.commands.list_queue import ListQueueCommand
from backend.src.application.encounters.use_cases.list_queue import ListQueue
from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.value_objects import EncounterStatus


@pytest.fixture()
def encounter_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def use_case(encounter_repository: AsyncMock) -> ListQueue:
    return ListQueue(encounter_repository=encounter_repository)


@pytest.mark.asyncio
async def test_execute_returns_queue_entries(
    use_case: ListQueue, encounter_repository: AsyncMock
) -> None:
    dept_id = uuid4()
    now = datetime.now(timezone.utc)
    encounter = Encounter(
        id=uuid4(),
        patient_id=uuid4(),
        department_id=dept_id,
        status=EncounterStatus.TRIAGED.value,
        esi_level=2,
        checked_in_at=now,
        created_at=now,
        updated_at=now,
    )
    encounter_repository.list_queue = AsyncMock(return_value=[encounter])

    result = await use_case.execute(ListQueueCommand(department_id=dept_id))

    encounter_repository.list_queue.assert_awaited_once_with(
        department_id=dept_id,
        statuses=[EncounterStatus.CHECKED_IN, EncounterStatus.TRIAGED],
    )
    assert len(result.entries) == 1
    assert result.entries[0].encounter_id == encounter.id
    assert result.entries[0].esi_level == 2


@pytest.mark.asyncio
async def test_execute_returns_empty_when_no_one_waiting(
    use_case: ListQueue, encounter_repository: AsyncMock
) -> None:
    encounter_repository.list_queue = AsyncMock(return_value=[])

    result = await use_case.execute(ListQueueCommand(department_id=uuid4()))

    assert result.entries == []
