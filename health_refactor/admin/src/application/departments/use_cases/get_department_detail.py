"""Use-case: get department details with users."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.infrastructure.database.models.department import (
    Department as DepartmentModel,
)
from backend.src.infrastructure.database.models.user import (
    User as UserModel,
)

_STATUS_DISPLAY: dict[str, str] = {
    "invited": "pending",
    "active": "active",
    "disabled": "disabled",
}


@dataclass
class DepartmentUser:
    email: str
    first_name: str
    last_name: str
    role: str


@dataclass
class DepartmentDetails:
    id: UUID
    name: str
    description: str | None
    status: str
    created_at: datetime
    users: list[DepartmentUser] = field(default_factory=list)


class GetDepartmentDetailUseCase:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, dept_id: UUID) -> DepartmentDetails | None:
        org_result = await self._session.execute(
            select(DepartmentModel).where(
                DepartmentModel.id == dept_id
            )
        )
        org = org_result.scalar_one_or_none()
        if org is None:
            return None

        users_result = await self._session.execute(
            select(UserModel)
            .where(UserModel.department_id == dept_id)
            .order_by(UserModel.created_at.asc())
        )
        users = [
            DepartmentUser(
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role,
            )
            for u in users_result.scalars().all()
        ]

        return DepartmentDetails(
            id=org.id,
            name=org.name,
            description=org.description,
            status=_STATUS_DISPLAY.get(org.status, org.status),
            created_at=org.created_at,
            users=users,
        )
