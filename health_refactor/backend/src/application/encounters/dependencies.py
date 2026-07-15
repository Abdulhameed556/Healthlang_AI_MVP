"""FastAPI dependency-injection providers for encounters use-cases."""
from fastapi import Depends

from backend.src.application.encounters.use_cases.check_in_patient import CheckInPatient
from backend.src.application.encounters.use_cases.discharge_encounter import (
    DischargeEncounter,
)
from backend.src.application.encounters.use_cases.get_encounter import GetEncounter
from backend.src.application.encounters.use_cases.list_queue import ListQueue
from backend.src.application.encounters.use_cases.mark_orders_fulfilled import (
    MarkOrdersFulfilled,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.patients.repositories import IPatientRepository
from backend.src.infrastructure.database.dependencies import (
    get_encounter_repository,
    get_patient_repository,
    get_unit_of_work,
)


def get_check_in_patient(
    patient_repository: IPatientRepository = Depends(get_patient_repository),
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> CheckInPatient:
    return CheckInPatient(
        patient_repository=patient_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


def get_get_encounter(
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
) -> GetEncounter:
    return GetEncounter(encounter_repository=encounter_repository)


def get_list_queue(
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
) -> ListQueue:
    return ListQueue(encounter_repository=encounter_repository)


def get_mark_orders_fulfilled(
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> MarkOrdersFulfilled:
    return MarkOrdersFulfilled(
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


def get_discharge_encounter(
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> DischargeEncounter:
    return DischargeEncounter(
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )
