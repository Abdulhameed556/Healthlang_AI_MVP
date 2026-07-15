"""Unit tests: application/prescriptions/use_cases/dispense_prescription.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from backend.src.application.prescriptions.commands.dispense_prescription import (
    DispensePrescriptionCommand,
)
from backend.src.application.prescriptions.use_cases.dispense_prescription import (
    DispensePrescription,
)
from backend.src.domain.inventory.entities import InventoryItem
from backend.src.domain.inventory.exceptions import InsufficientStockError
from backend.src.domain.prescriptions.entities import Prescription
from backend.src.domain.prescriptions.exceptions import (
    PrescriptionAlreadyDispensedError,
    PrescriptionNotFoundError,
)
from backend.src.domain.prescriptions.value_objects import PrescriptionStatus


def _prescription(
    status: PrescriptionStatus = PrescriptionStatus.PENDING,
    inventory_item_id=None,
) -> Prescription:
    now = datetime.now(timezone.utc)
    return Prescription(
        id=uuid4(),
        encounter_id=uuid4(),
        ordered_by=uuid4(),
        inventory_item_id=inventory_item_id or uuid4(),
        dosage="500mg twice daily",
        status=status.value,
        created_at=now,
        updated_at=now,
    )


def _item(quantity_on_hand: int) -> InventoryItem:
    now = datetime.now(timezone.utc)
    return InventoryItem(
        id=uuid4(),
        department_id=uuid4(),
        drug_name="Paracetamol 500mg",
        quantity_on_hand=quantity_on_hand,
        reorder_threshold=10,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture()
def prescription_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda p: p)
    return repo


@pytest.fixture()
def inventory_item_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.save = AsyncMock(side_effect=lambda item: item)
    return repo


@pytest.fixture()
def unit_of_work() -> AsyncMock:
    uow = AsyncMock()
    uow.commit = AsyncMock()
    return uow


@pytest.fixture()
def use_case(prescription_repository, inventory_item_repository, unit_of_work) -> DispensePrescription:
    return DispensePrescription(
        prescription_repository=prescription_repository,
        inventory_item_repository=inventory_item_repository,
        unit_of_work=unit_of_work,
    )


@pytest.mark.asyncio
async def test_execute_dispenses_and_decrements_stock(
    use_case: DispensePrescription,
    prescription_repository,
    inventory_item_repository,
    unit_of_work,
) -> None:
    item = _item(quantity_on_hand=10)
    prescription = _prescription(inventory_item_id=item.id)
    prescription_repository.get_by_id = AsyncMock(return_value=prescription)
    inventory_item_repository.get_by_id = AsyncMock(return_value=item)

    result = await use_case.execute(
        DispensePrescriptionCommand(prescription_id=prescription.id, dispensed_by=uuid4())
    )

    assert result.status == PrescriptionStatus.DISPENSED.value
    assert result.remaining_stock == 9
    saved_item: InventoryItem = inventory_item_repository.save.await_args.args[0]
    assert saved_item.quantity_on_hand == 9
    unit_of_work.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_execute_raises_when_prescription_missing(
    use_case: DispensePrescription, prescription_repository
) -> None:
    prescription_repository.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(PrescriptionNotFoundError):
        await use_case.execute(
            DispensePrescriptionCommand(prescription_id=uuid4(), dispensed_by=uuid4())
        )


@pytest.mark.asyncio
async def test_execute_rejects_already_dispensed(
    use_case: DispensePrescription, prescription_repository
) -> None:
    prescription = _prescription(status=PrescriptionStatus.DISPENSED)
    prescription_repository.get_by_id = AsyncMock(return_value=prescription)

    with pytest.raises(PrescriptionAlreadyDispensedError):
        await use_case.execute(
            DispensePrescriptionCommand(
                prescription_id=prescription.id, dispensed_by=uuid4()
            )
        )


@pytest.mark.asyncio
async def test_execute_rejects_insufficient_stock(
    use_case: DispensePrescription, prescription_repository, inventory_item_repository
) -> None:
    item = _item(quantity_on_hand=0)
    prescription = _prescription(inventory_item_id=item.id)
    prescription_repository.get_by_id = AsyncMock(return_value=prescription)
    inventory_item_repository.get_by_id = AsyncMock(return_value=item)

    with pytest.raises(InsufficientStockError):
        await use_case.execute(
            DispensePrescriptionCommand(
                prescription_id=prescription.id, dispensed_by=uuid4()
            )
        )
    inventory_item_repository.save.assert_not_awaited()
    prescription_repository.save.assert_not_awaited()
