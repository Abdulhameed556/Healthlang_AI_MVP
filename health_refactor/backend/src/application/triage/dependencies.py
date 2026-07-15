"""FastAPI dependency-injection providers for triage use-cases."""
from fastapi import Depends

from backend.src.application.triage.use_cases.get_triage_record import GetTriageRecord
from backend.src.application.triage.use_cases.record_triage import RecordTriage
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.triage.repositories import ITriageRecordRepository
from backend.src.infrastructure.database.dependencies import (
    get_encounter_repository,
    get_triage_record_repository,
    get_unit_of_work,
)


def get_record_triage(
    triage_repository: ITriageRecordRepository = Depends(get_triage_record_repository),
    encounter_repository: IEncounterRepository = Depends(get_encounter_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> RecordTriage:
    return RecordTriage(
        triage_repository=triage_repository,
        encounter_repository=encounter_repository,
        unit_of_work=unit_of_work,
    )


def get_get_triage_record(
    triage_repository: ITriageRecordRepository = Depends(get_triage_record_repository),
) -> GetTriageRecord:
    return GetTriageRecord(triage_repository=triage_repository)
