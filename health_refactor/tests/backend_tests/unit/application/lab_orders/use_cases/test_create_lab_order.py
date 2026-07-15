"""Unit tests: application/lab_orders/use_cases/create_lab_order.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.lab_orders.commands.create_lab_order import (
    CreateLabOrderCommand,
)
from backend.src.application.lab_orders.use_cases.create_lab_order import CreateLabOrder
from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.lab_orders.value_objects import LabOrderStatus


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


@pytest.fixture()
def lab_order_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda order: order)
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
def use_case(lab_order_repository, encounter_repository, unit_of_work) -> CreateLabOrder:
    return CreateLabOrder(
        lab_order_repository=lab_order_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


@pytest.mark.asyncio
async def test_execute_advances_in_consultation_to_order_placed(
    use_case: CreateLabOrder, encounter_repository, unit_of_work
) -> None:
    encounter = _encounter(EncounterStatus.IN_CONSULTATION)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    result = await use_case.execute(
        CreateLabOrderCommand(
            encounter_id=encounter.id, ordered_by=uuid4(), test_type="Full blood count"
        )
    )

    assert result.status == LabOrderStatus.PENDING.value
    saved_encounter: Encounter = encounter_repository.save.await_args.args[0]
    assert saved_encounter.status == EncounterStatus.ORDER_PLACED.value
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_adds_second_order_without_retransitioning(
    use_case: CreateLabOrder, encounter_repository
) -> None:
    encounter = _encounter(EncounterStatus.ORDER_PLACED)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    await use_case.execute(
        CreateLabOrderCommand(
            encounter_id=encounter.id, ordered_by=uuid4(), test_type="Malaria RDT"
        )
    )

    encounter_repository.save.assert_not_awaited()


@pytest.mark.asyncio
async def test_execute_raises_when_encounter_missing(
    use_case: CreateLabOrder, encounter_repository
) -> None:
    encounter_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(EncounterNotFoundError):
        await use_case.execute(
            CreateLabOrderCommand(encounter_id=uuid4(), ordered_by=uuid4(), test_type="x")
        )


@pytest.mark.asyncio
async def test_execute_rejects_order_before_consultation(
    use_case: CreateLabOrder, encounter_repository
) -> None:
    encounter = _encounter(EncounterStatus.TRIAGED)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)

    with pytest.raises(ValidationError, match="Cannot place an order"):
        await use_case.execute(
            CreateLabOrderCommand(encounter_id=encounter.id, ordered_by=uuid4(), test_type="x")
        )
