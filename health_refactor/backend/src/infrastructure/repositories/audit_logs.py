"""SQLAlchemy implementation of IAuditLogRepository."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.audit.entities import AuditLog
from backend.src.domain.audit.repositories import IAuditLogRepository
from backend.src.infrastructure.database.models.audit_log import AuditLog as AuditLogModel
from backend.src.infrastructure.repositories._mappers import (
    audit_log_to_entity,
    audit_log_to_model,
)


class SqlAlchemyAuditLogRepository(IAuditLogRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, log: AuditLog) -> AuditLog:
        model = audit_log_to_model(log)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return audit_log_to_entity(model)

    async def list_all(
        self, *, page: int, page_size: int
    ) -> tuple[list[AuditLog], int]:
        return await self._list(filter_clause=None, page=page, page_size=page_size)

    async def list_by_department_id(
        self, department_id: UUID, *, page: int, page_size: int
    ) -> tuple[list[AuditLog], int]:
        return await self._list(
            filter_clause=(AuditLogModel.department_id == department_id),
            page=page,
            page_size=page_size,
        )

    async def _list(
        self, *, filter_clause, page: int, page_size: int
    ) -> tuple[list[AuditLog], int]:
        query = select(AuditLogModel)
        count_query = select(func.count()).select_from(AuditLogModel)
        if filter_clause is not None:
            query = query.where(filter_clause)
            count_query = count_query.where(filter_clause)

        total = (await self._session.execute(count_query)).scalar_one()
        result = await self._session.execute(
            query.order_by(AuditLogModel.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        logs = [audit_log_to_entity(model) for model in result.scalars().all()]
        return logs, total
