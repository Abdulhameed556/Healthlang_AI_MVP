"""Use-case: register (or reuse) a patient and open a new encounter for them."""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.application.encounters.commands.check_in_patient import (
    CheckInPatientCommand,
)
from backend.src.application.encounters.results.check_in_patient import (
    CheckInPatientResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.core.exceptions import ValidationError
from backend.src.domain.encounters.entities import Encounter
from backend.src.domain.encounters.repositories import IEncounterRepository
from backend.src.domain.encounters.value_objects import EncounterStatus
from backend.src.domain.patients.entities import Patient
from backend.src.domain.patients.exceptions import PatientNotFoundError
from backend.src.domain.patients.repositories import IPatientRepository
from backend.src.domain.patients.value_objects import InsuranceStatus

_NEW_PATIENT_REQUIRED_FIELDS = (
    "first_name",
    "last_name",
    "date_of_birth",
    "sex",
    "phone_number",
)


class CheckInPatient:
    def __init__(
        self,
        patient_repository: IPatientRepository,
        encounter_repository: IEncounterRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._patient_repository = patient_repository
        self._encounter_repository = encounter_repository
        self._unit_of_work = unit_of_work

    async def execute(self, command: CheckInPatientCommand) -> CheckInPatientResult:
        patient = await self._resolve_patient(command)

        now = datetime.now(timezone.utc)
        encounter = Encounter(
            id=uuid4(),
            patient_id=patient.id,
            department_id=command.department_id,
            status=EncounterStatus.CHECKED_IN.value,
            checked_in_at=now,
            created_at=now,
            updated_at=now,
        )
        encounter = await self._encounter_repository.add(encounter)
        await self._unit_of_work.commit()

        return CheckInPatientResult(
            encounter_id=encounter.id,
            patient_id=patient.id,
            department_id=encounter.department_id,
            status=encounter.status,
            checked_in_at=encounter.checked_in_at,
        )

    async def _resolve_patient(self, command: CheckInPatientCommand) -> Patient:
        if command.patient_id is not None:
            patient = await self._patient_repository.get_by_id(command.patient_id)
            if patient is None:
                raise PatientNotFoundError("Patient not found")
            return patient

        missing = [
            field
            for field in _NEW_PATIENT_REQUIRED_FIELDS
            if getattr(command, field) is None
        ]
        if missing:
            raise ValidationError(
                f"New patient check-in requires: {', '.join(missing)}"
            )

        now = datetime.now(timezone.utc)
        patient = Patient(
            id=uuid4(),
            first_name=command.first_name,
            last_name=command.last_name,
            date_of_birth=command.date_of_birth,
            sex=command.sex,
            phone_number=command.phone_number,
            next_of_kin_name=command.next_of_kin_name,
            next_of_kin_phone=command.next_of_kin_phone,
            insurance_status=command.insurance_status or InsuranceStatus.NONE.value,
            created_at=now,
            updated_at=now,
        )
        return await self._patient_repository.add(patient)
