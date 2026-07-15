"""Use-case: look up a patient by id."""
from backend.src.application.patients.commands.get_patient import GetPatientCommand
from backend.src.application.patients.results.get_patient import GetPatientResult
from backend.src.domain.patients.exceptions import PatientNotFoundError
from backend.src.domain.patients.repositories import IPatientRepository


class GetPatient:
    def __init__(self, patient_repository: IPatientRepository) -> None:
        self._patient_repository = patient_repository

    async def execute(self, command: GetPatientCommand) -> GetPatientResult:
        patient = await self._patient_repository.get_by_id(command.patient_id)
        if patient is None:
            raise PatientNotFoundError("Patient not found")

        return GetPatientResult(
            patient_id=patient.id,
            first_name=patient.first_name,
            last_name=patient.last_name,
            date_of_birth=patient.date_of_birth,
            sex=patient.sex,
            phone_number=patient.phone_number,
            insurance_status=patient.insurance_status,
            next_of_kin_name=patient.next_of_kin_name,
            next_of_kin_phone=patient.next_of_kin_phone,
        )
