"""Use-case: list an encounter's prescriptions, oldest first."""
from backend.src.application.prescriptions.commands.list_prescriptions import (
    ListPrescriptionsCommand,
)
from backend.src.application.prescriptions.results.list_prescriptions import (
    ListPrescriptionsResult,
    PrescriptionSummary,
)
from backend.src.domain.prescriptions.repositories import IPrescriptionRepository


class ListPrescriptions:
    def __init__(self, prescription_repository: IPrescriptionRepository) -> None:
        self._prescription_repository = prescription_repository

    async def execute(
        self, command: ListPrescriptionsCommand
    ) -> ListPrescriptionsResult:
        prescriptions = await self._prescription_repository.list_by_encounter_id(
            command.encounter_id
        )
        return ListPrescriptionsResult(
            prescriptions=[
                PrescriptionSummary(
                    prescription_id=p.id,
                    inventory_item_id=p.inventory_item_id,
                    dosage=p.dosage,
                    status=p.status,
                    created_at=p.created_at,
                    dispensed_at=p.dispensed_at,
                )
                for p in prescriptions
            ]
        )
