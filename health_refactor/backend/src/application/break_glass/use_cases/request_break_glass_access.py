"""Use-case: a clinician requests emergency access to a patient outside their
normal scope.

Unlike the general-purpose audit middleware (which logs after the fact, in
its own transaction), this writes the BreakGlassAccess row and its AuditLog
twin in the *same* transaction — break-glass is the single most
audit-sensitive action in the system, so the two must succeed or fail
together, not just "probably both happen."
"""
from datetime import datetime, timezone
from uuid import uuid4

from backend.src.application.break_glass.commands.request_break_glass_access import (
    RequestBreakGlassAccessCommand,
)
from backend.src.application.break_glass.results.request_break_glass_access import (
    RequestBreakGlassAccessResult,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.audit.entities import AuditLog
from backend.src.domain.audit.repositories import IAuditLogRepository
from backend.src.domain.audit.value_objects import AuditOutcome
from backend.src.domain.break_glass.entities import BreakGlassAccess
from backend.src.domain.break_glass.repositories import IBreakGlassAccessRepository
from backend.src.domain.patients.exceptions import PatientNotFoundError
from backend.src.domain.patients.repositories import IPatientRepository

_ACTION = "break_glass_access_requested"


class RequestBreakGlassAccess:
    def __init__(
        self,
        break_glass_repository: IBreakGlassAccessRepository,
        patient_repository: IPatientRepository,
        audit_log_repository: IAuditLogRepository,
        unit_of_work: IUnitOfWork,
    ) -> None:
        self._break_glass_repository = break_glass_repository
        self._patient_repository = patient_repository
        self._audit_log_repository = audit_log_repository
        self._unit_of_work = unit_of_work

    async def execute(
        self, command: RequestBreakGlassAccessCommand
    ) -> RequestBreakGlassAccessResult:
        patient = await self._patient_repository.get_by_id(command.target_patient_id)
        if patient is None:
            raise PatientNotFoundError("Patient not found")

        now = datetime.now(timezone.utc)
        request = BreakGlassAccess(
            id=uuid4(),
            requesting_user_id=command.requesting_user_id,
            target_patient_id=command.target_patient_id,
            reason=command.reason,
            needs_review=True,
            created_at=now,
        )
        request = await self._break_glass_repository.add(request)

        await self._audit_log_repository.add(
            AuditLog(
                id=uuid4(),
                actor_id=command.requesting_user_id,
                actor_role=command.requesting_user_role,
                action=_ACTION,
                target_entity_id=str(command.target_patient_id),
                ip_address=command.ip_address,
                outcome=AuditOutcome.SUCCESS.value,
                created_at=now,
            )
        )
        await self._unit_of_work.commit()

        return RequestBreakGlassAccessResult(
            request_id=request.id,
            target_patient_id=request.target_patient_id,
            needs_review=request.needs_review,
            created_at=request.created_at,
        )
