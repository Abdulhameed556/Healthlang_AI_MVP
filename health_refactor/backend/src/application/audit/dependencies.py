"""FastAPI dependency-injection providers for audit use-cases."""
from fastapi import Depends

from backend.src.application.audit.use_cases.list_audit_log import ListAuditLog
from backend.src.domain.audit.repositories import IAuditLogRepository
from backend.src.infrastructure.database.dependencies import get_audit_log_repository


def get_list_audit_log(
    audit_log_repository: IAuditLogRepository = Depends(get_audit_log_repository),
) -> ListAuditLog:
    return ListAuditLog(audit_log_repository=audit_log_repository)
