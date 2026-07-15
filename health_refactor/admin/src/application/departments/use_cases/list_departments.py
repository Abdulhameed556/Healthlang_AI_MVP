"""Use-case: list all departments with activation status."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infrastructure.database.models.department import (
    Department as DepartmentModel,
)

_STATUS_DISPLAY: dict[str, str] = {
    "invited": "pending",
    "active": "active",
    "disabled": "disabled",
}


@dataclass
class DepartmentSummary:
    id: UUID
    name: str
    status: str
    created_at: datetime


class ListDepartmentsUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self) -> list[DepartmentSummary]:
        result = await self._session.execute(
            select(DepartmentModel).order_by(
                DepartmentModel.created_at.desc()
            )
        )
        return [
            DepartmentSummary(
                id=m.id,
                name=m.name,
                status=_STATUS_DISPLAY.get(m.status, m.status),
                created_at=m.created_at,
            )
            for m in result.scalars().all()
        ]
