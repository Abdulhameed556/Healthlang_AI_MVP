"""FastAPI dependency-injection providers for prescriptions use-cases."""
from fastapi import Depends

from backend.src.application.prescriptions.use_cases.create_prescription import (
    CreatePrescription,
)
from backend.src.application.prescriptions.use_cases.dispense_prescription import (
    DispensePrescription,
)
from backend.src.application.prescriptions.use_cases.list_prescriptions import (
    ListPrescriptions,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.inventory.repositories import IInventoryItemRepository
from backend.src.domain.prescriptions.repositories import IPrescriptionRepository
from backend.src.infrastructure.database.dependencies import (
    get_encounter_repository,
    get_inventory_item_repository,
    get_prescription_repository,
    get_unit_of_work,
)


def get_create_prescription(
    prescription_repository: IPrescriptionRepository = Depends(get_prescription_repository),
    inventory_item_repository: IInventoryItemRepository = Depends(
        get_inventory_item_repository
    ),
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CreatePrescription:
    return CreatePrescription(
        prescription_repository=prescription_repository,
        inventory_item_repository=inventory_item_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


def get_dispense_prescription(
    prescription_repository: IPrescriptionRepository = Depends(get_prescription_repository),
    inventory_item_repository: IInventoryItemRepository = Depends(
        get_inventory_item_repository
    ),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> DispensePrescription:
    return DispensePrescription(
        prescription_repository=prescription_repository,
        inventory_item_repository=inventory_item_repository,
        unit_of_work=unit_of_work,
    )


def get_list_prescriptions(
    prescription_repository: IPrescriptionRepository = Depends(get_prescription_repository),
) -> ListPrescriptions:
    return ListPrescriptions(prescription_repository=prescription_repository)
