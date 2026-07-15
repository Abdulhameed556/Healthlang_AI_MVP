"""Use-case: doctor prescribes a medication for an encounter."""
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.application.prescriptions.commands.create_prescription import (
    CreatePrescriptionCommand,
)
from backend.src.application.prescriptions.results.create_prescription import (
    CreatePrescriptionResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.state_machine import (
    assert_can_place_order,
    assert_valid_transition,
)
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.inventory.exceptions import InventoryItemNotFoundError
from backend.src.domain.inventory.repositories import IInventoryItemRepository
from backend.src.domain.prescriptions.entities import Prescription
from backend.src.domain.prescriptions.repositories import IPrescriptionRepository
from backend.src.domain.prescriptions.value_objects import PrescriptionStatus


class CreatePrescription:
    def __init__(
        self,
        prescription_repository: IPrescriptionRepository,
        inventory_item_repository: IInventoryItemRepository,
        encounter_repository: IEncounterRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._prescription_repository = prescription_repository
        self._inventory_item_repository = inventory_item_repository
        self._encounter_repository = encounter_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: CreatePrescriptionCommand
    ) -> CreatePrescriptionResult:
        encounter = await self._encounter_repository.get_by_id(command.encounter_id)
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")

        item = await self._inventory_item_repository.get_by_id(
            command.inventory_item_id
        )
        if item is None:
            raise InventoryItemNotFoundError("Inventory item not found")

        status = EncounterStatus(encounter.status)
        assert_can_place_order(status)

        now = datetime.now(timezone.utc)
        if status == EncounterStatus.IN_CONSULTATION:
            assert_valid_transition(status, EncounterStatus.ORDER_PLACED)
            updated_encounter = replace(
                encounter, status=EncounterStatus.ORDER_PLACED.value, updated_at=now
            )
            await self._encounter_repository.save(updated_encounter)

        prescription = Prescription(
            id=uuid4(),
            encounter_id=command.encounter_id,
            ordered_by=command.ordered_by,
            inventory_item_id=command.inventory_item_id,
            dosage=command.dosage,
            status=PrescriptionStatus.PENDING.value,
            created_at=now,
            updated_at=now,
        )
        prescription = await self._prescription_repository.add(prescription)
        await self._unit_of_work.commit()

        return CreatePrescriptionResult(
            prescription_id=prescription.id,
            encounter_id=prescription.encounter_id,
            inventory_item_id=prescription.inventory_item_id,
            dosage=prescription.dosage,
            status=prescription.status,
        )
