"""Use-case: doctor orders a lab test for an encounter."""
from dataclasses import replace
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.application.lab_orders.commands.create_lab_order import (
    CreateLabOrderCommand,
)
from backend.src.application.lab_orders.results.create_lab_order import (
    CreateLabOrderResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.exceptions import EncounterNotFoundError
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.state_machine import (
    assert_can_place_order,
    assert_valid_transition,
)
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.lab_orders.entities import LabOrder
from backend.src.domain.lab_orders.repositories import ILabOrderRepository
from backend.src.domain.lab_orders.value_objects import LabOrderStatus


class CreateLabOrder:
    def __init__(
        self,
        lab_order_repository: ILabOrderRepository,
        encounter_repository: IEncounterRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._lab_order_repository = lab_order_repository
        self._encounter_repository = encounter_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: CreateLabOrderCommand) -> CreateLabOrderResult:
        encounter = await self._encounter_repository.get_by_id(command.encounter_id)
        if encounter is None:
            raise EncounterNotFoundError("Encounter not found")

        status = EncounterStatus(encounter.status)
        assert_can_place_order(status)

        now = datetime.now(timezone.utc)
        if status == EncounterStatus.IN_CONSULTATION:
            assert_valid_transition(status, EncounterStatus.ORDER_PLACED)
            updated_encounter = replace(
                encounter, status=EncounterStatus.ORDER_PLACED.value, updated_at=now
            )
            await self._encounter_repository.save(updated_encounter)

        lab_order = LabOrder(
            id=uuid4(),
            encounter_id=command.encounter_id,
            ordered_by=command.ordered_by,
            test_type=command.test_type,
            status=LabOrderStatus.PENDING.value,
            created_at=now,
            updated_at=now,
        )
        lab_order = await self._lab_order_repository.add(lab_order)
        await self._unit_of_work.commit()

        return CreateLabOrderResult(
            lab_order_id=lab_order.id,
            encounter_id=lab_order.encounter_id,
            test_type=lab_order.test_type,
            status=lab_order.status,
        )
