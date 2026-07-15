"""FastAPI DI providers for departments use-cases."""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from admin.src.application.departments.use_cases.get_department_detail import (  # noqa: E501
    GetDepartmentDetailUseCase,
)
from admin.src.application.departments.use_cases.invite_product_user import (
    InviteProductUserUseCase,
)
from admin.src.application.departments.use_cases.list_departments import (
    ListDepartmentsUseCase,
)
from backend.src.application.users.dependencies.providers import (
    get_create_invited_user_from_admin,
)
from backend.src.application.users.use_cases.create_invited_user_from_admin import (  # noqa: E501
    CreateInvitedUserFromAdmin,
)
from backend.src.infrastructure.database.dependencies import get_db


def get_invite_product_user_use_case(
    create_invited_user: CreateInvitedUserFromAdmin = Depends(
        get_create_invited_user_from_admin
    ),
) -> InviteProductUserUseCase:
    return InviteProductUserUseCase(create_invited_user=create_invited_user)


def get_list_departments_use_case(
    session: AsyncSession = Depends(get_db),
) -> ListDepartmentsUseCase:
    return ListDepartmentsUseCase(session=session)


def get_department_detail_use_case(
    session: AsyncSession = Depends(get_db),
) -> GetDepartmentDetailUseCase:
    return GetDepartmentDetailUseCase(session=session)
