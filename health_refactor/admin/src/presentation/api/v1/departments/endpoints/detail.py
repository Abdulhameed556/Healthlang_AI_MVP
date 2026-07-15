"""Endpoint: get department detail (Admin-only)."""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.departments.dependencies import (
    get_department_detail_use_case,
)
from admin.src.application.departments.use_cases.get_department_detail import (  # noqa: E501
    GetDepartmentDetailUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.departments.schemas import (
    DepartmentDetailResponse,
    DepartmentUserItem,
)

router = APIRouter()


@router.get(
    "/{dept_id}",
    response_model=DepartmentDetailResponse,
    summary="Get department details",
    description=(
        "Admin-only. Returns full department details including description, "
        "status, and a list of all users (email, name, role)."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not an admin (read_only)."},
        404: {"description": "Department not found."},
    },
)
async def get_department(
    dept_id: UUID,
    use_case: GetDepartmentDetailUseCase = Depends(
        get_department_detail_use_case
    ),
    _: AdminUser = Depends(require_admin),
) -> DepartmentDetailResponse:
    details = await use_case.execute(dept_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Department not found.")
    return DepartmentDetailResponse(
        id=details.id,
        name=details.name,
        description=details.description,
        status=details.status,
        created_at=details.created_at,
        users=[
            DepartmentUserItem(
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                role=u.role,
            )
            for u in details.users
        ],
    )
