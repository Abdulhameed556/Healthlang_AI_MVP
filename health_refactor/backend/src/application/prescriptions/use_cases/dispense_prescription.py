"""Use-case: pharmacist dispenses a pending prescription.

Decrements the referenced inventory item by one unit in the same transaction
as marking the prescription dispensed — the two must succeed or fail together.
"""
from dataclasses import replace
from datetime import datetime, timezone

from backend.src.application.prescriptions.commands.dispense_prescription import (
    DispensePrescriptionCommand,
)
from backend.src.application.prescriptions.results.dispense_prescription import (
    DispensePrescriptionResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.inventory.exceptions import InventoryItemNotFoundError
from backend.src.domain.inventory.repositories import IInventoryItemRepository
from backend.src.domain.inventory.rules import assert_sufficient_stock
from backend.src.domain.prescriptions.exceptions import (
    PrescriptionAlreadyDispensedError,
    PrescriptionNotFoundError,
)
from backend.src.domain.prescriptions.repositories import IPrescriptionRepository
from backend.src.domain.prescriptions.value_objects import PrescriptionStatus

_DISPENSE_QUANTITY = 1


class DispensePrescription:
    def __init__(
        self,
        prescription_repository: IPrescriptionRepository,
        inventory_item_repository: IInventoryItemRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._prescription_repository = prescription_repository
        self._inventory_item_repository = inventory_item_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: DispensePrescriptionCommand
    ) -> DispensePrescriptionResult:
        prescription = await self._prescription_repository.get_by_id(
            command.prescription_id
        )
        if prescription is None:
            raise PrescriptionNotFoundError("Prescription not found")

        if prescription.status == PrescriptionStatus.DISPENSED.value:
            raise PrescriptionAlreadyDispensedError(
                "This prescription is already dispensed"
            )

        item = await self._inventory_item_repository.get_by_id(
            prescription.inventory_item_id
        )
        if item is None:
            raise InventoryItemNotFoundError("Inventory item not found")

        assert_sufficient_stock(item, _DISPENSE_QUANTITY)

        updated_item = replace(
            item,
            quantity_on_hand=item.quantity_on_hand - _DISPENSE_QUANTITY,
            updated_at=datetime.now(timezone.utc),
        )
        updated_item = await self._inventory_item_repository.save(updated_item)

        now = datetime.now(timezone.utc)
        updated_prescription = replace(
            prescription,
            status=PrescriptionStatus.DISPENSED.value,
            dispensed_by=command.dispensed_by,
            dispensed_at=now,
            updated_at=now,
        )
        updated_prescription = await self._prescription_repository.save(
            updated_prescription
        )
        await self._unit_of_work.commit()

        return DispensePrescriptionResult(
            prescription_id=updated_prescription.id,
            status=updated_prescription.status,
            dispensed_at=updated_prescription.dispensed_at,
            remaining_stock=updated_item.quantity_on_hand,
        )
