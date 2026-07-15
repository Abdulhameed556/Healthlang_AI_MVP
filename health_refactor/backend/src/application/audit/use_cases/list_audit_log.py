"""Use-case: list the audit log, scoped by the viewer's role.

super_admin sees every department's entries; admin sees only their own
department's. Every other role is refused before any query runs.
"""
from backend.src.application.audit.commands.list_audit_log import ListAuditLogCommand
from backend.src.application.audit.results.list_audit_log import (
    AuditLogEntry,
    ListAuditLogResult,
)
from backend.src.core.pagination import total_pages
from backend.src.domain.access_control.rules import (
    assert_can_view_audit_log,
    scoped_department_id,
)
from backend.src.domain.audit.repositories import IAuditLogRepository


class ListAuditLog:
    def __init__(self, audit_log_repository: IAuditLogRepository) -> None:
        self._audit_log_repository = audit_log_repository

    async def execute(self, command: ListAuditLogCommand) -> ListAuditLogResult:
        assert_can_view_audit_log(command.viewer_role)

        department_id = scoped_department_id(
            viewer_role=command.viewer_role,
            viewer_department_id=command.viewer_department_id,
        )
        if department_id is None:
            logs, total = await self._audit_log_repository.list_all(
                page=command.page, page_size=command.page_size
            )
        else:
            logs, total = await self._audit_log_repository.list_by_department_id(
                department_id, page=command.page, page_size=command.page_size
            )

        return ListAuditLogResult(
            logs=[
                AuditLogEntry(
                    log_id=log.id,
                    actor_id=log.actor_id,
                    actor_role=log.actor_role,
                    department_id=log.department_id,
                    action=log.action,
                    target_entity_id=log.target_entity_id,
                    ip_address=log.ip_address,
                    outcome=log.outcome,
                    created_at=log.created_at,
                )
                for log in logs
            ],
            total=total,
            page=command.page,
            page_size=command.page_size,
            total_pages=total_pages(total, command.page_size),
        )
