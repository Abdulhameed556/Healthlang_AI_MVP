"""Abstract repository interface for audit logs."""
from typing import Protocol
from uuid import UUID

from backend.src.domain.audit.entities import AuditLog


class IAuditLogRepository(Protocol):
    async def add(self, log: AuditLog) -> AuditLog: ...

    async def list_all(
        self, *, page: int, page_size: int
    ) -> tuple[list[AuditLog], int]: ...

    async def list_by_department_id(
        self, department_id: UUID, *, page: int, page_size: int
    ) -> tuple[list[AuditLog], int]: ...
