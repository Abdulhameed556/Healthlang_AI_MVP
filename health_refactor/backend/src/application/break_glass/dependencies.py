"""FastAPI dependency-injection providers for break_glass use-cases."""
from fastapi import Depends

from backend.src.application.break_glass.use_cases.list_break_glass_access import (
    ListBreakGlassAccess,
)
from backend.src.application.break_glass.use_cases.request_break_glass_access import (
    RequestBreakGlassAccess,
)
from backend.src.application.break_glass.use_cases.review_break_glass_access import (
    ReviewBreakGlassAccess,
)
from backend.src.application.users.ports.unit_of_work import IUnitOfWork
from backend.src.domain.audit.repositories import IAuditLogRepository
from backend.src.domain.break_glass.repositories import IBreakGlassAccessRepository
from backend.src.domain.patients.repositories import IPatientRepository
from backend.src.infrastructure.database.dependencies import (
    get_audit_log_repository,
    get_break_glass_access_repository,
    get_patient_repository,
    get_unit_of_work,
)


def get_request_break_glass_access(
    break_glass_repository: IBreakGlassAccessRepository = Depends(
        get_break_glass_access_repository
    ),
    patient_repository: IPatientRepository = Depends(get_patient_repository),
    audit_log_repository: IAuditLogRepository = Depends(get_audit_log_repository),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> RequestBreakGlassAccess:
    return RequestBreakGlassAccess(
        break_glass_repository=break_glass_repository,
        patient_repository=patient_repository,
        audit_log_repository=audit_log_repository,
        unit_of_work=unit_of_work,
    )


def get_list_break_glass_access(
    break_glass_repository: IBreakGlassAccessRepository = Depends(
        get_break_glass_access_repository
    ),
) -> ListBreakGlassAccess:
    return ListBreakGlassAccess(break_glass_repository=break_glass_repository)


def get_review_break_glass_access(
    break_glass_repository: IBreakGlassAccessRepository = Depends(
        get_break_glass_access_repository
    ),
    unit_of_work: IUnitOfWork = Depends(get_unit_of_work),
) -> ReviewBreakGlassAccess:
    return ReviewBreakGlassAccess(
        break_glass_repository=break_glass_repository,
        unit_of_work=unit_of_work,
    )
