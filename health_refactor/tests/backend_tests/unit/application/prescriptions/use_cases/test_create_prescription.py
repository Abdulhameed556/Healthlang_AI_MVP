"""Unit tests: application/prescriptions/use_cases/create_prescription.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.prescriptions.commands.create_prescription import (
    CreatePrescriptionCommand,
)
from backend.src.application.prescriptions.use_cases.create_prescription import (
    CreatePrescription,
)
from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.inventory.entities import InventoryItem
from backend.src.domain.inventory.exceptions import InventoryItemNotFoundError
from backend.src.domain.prescriptions.value_objects import PrescriptionStatus


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


def _inventory_item() -> InventoryItem:
    now = datetime.now(timezone.utc)
    return InventoryItem(
        id=uuid4(),
        department_id=uuid4(),
        drug_name="Paracetamol 500mg",
        quantity_on_hand=50,
        reorder_threshold=10,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture()
def prescription_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.add = AsyncMock(side_effect=lambda p: p)
    return repo


@pytest.fixture()
def inventory_item_repository() -> AsyncMock:
    return AsyncMock()


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
def use_case(
    prescription_repository, inventory_item_repository, encounter_repository, unit_of_work
) -> CreatePrescription:
    return CreatePrescription(
        prescription_repository=prescription_repository,
        inventory_item_repository=inventory_item_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


@pytest.mark.asyncio
async def test_execute_advances_in_consultation_to_order_placed(
    use_case: CreatePrescription,
    encounter_repository,
    inventory_item_repository,
    unit_of_work,
) -> None:
    encounter = _encounter(EncounterStatus.IN_CONSULTATION)
    item = _inventory_item()
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)
    inventory_item_repository.get_by_id = AsyncMock(return_value=item)

    result = await use_case.execute(
        CreatePrescriptionCommand(
            encounter_id=encounter.id,
            ordered_by=uuid4(),
            inventory_item_id=item.id,
            dosage="500mg twice daily",
        )
    )

    assert result.status == PrescriptionStatus.PENDING.value
    saved_encounter: Encounter = encounter_repository.save.await_args.args[0]
    assert saved_encounter.status == EncounterStatus.ORDER_PLACED.value
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_raises_when_encounter_missing(
    use_case: CreatePrescription, encounter_repository
) -> None:
    encounter_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(EncounterNotFoundError):
        await use_case.execute(
            CreatePrescriptionCommand(
                encounter_id=uuid4(),
                ordered_by=uuid4(),
                inventory_item_id=uuid4(),
                dosage="x",
            )
        )


@pytest.mark.asyncio
async def test_execute_raises_when_inventory_item_missing(
    use_case: CreatePrescription, encounter_repository, inventory_item_repository
) -> None:
    encounter = _encounter(EncounterStatus.IN_CONSULTATION)
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)
    inventory_item_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(InventoryItemNotFoundError):
        await use_case.execute(
            CreatePrescriptionCommand(
                encounter_id=encounter.id,
                ordered_by=uuid4(),
                inventory_item_id=uuid4(),
                dosage="x",
            )
        )


@pytest.mark.asyncio
async def test_execute_rejects_order_before_consultation(
    use_case: CreatePrescription, encounter_repository, inventory_item_repository
) -> None:
    encounter = _encounter(EncounterStatus.TRIAGED)
    item = _inventory_item()
    encounter_repository.get_by_id = AsyncMock(return_value=encounter)
    inventory_item_repository.get_by_id = AsyncMock(return_value=item)

    with pytest.raises(ValidationError, match="Cannot place an order"):
        await use_case.execute(
            CreatePrescriptionCommand(
                encounter_id=encounter.id,
                ordered_by=uuid4(),
                inventory_item_id=item.id,
                dosage="x",
            )
        )
