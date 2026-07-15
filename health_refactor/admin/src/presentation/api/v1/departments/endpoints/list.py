"""Endpoint: list all departments (Admin-only)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from admin.src.application.auth.dependencies import require_admin
from admin.src.application.departments.dependencies import (
    get_list_departments_use_case,
)
from admin.src.application.departments.use_cases.list_departments import (
    ListDepartmentsUseCase,
)
from admin.src.domain.users.entities import AdminUser
from admin.src.presentation.api.v1.departments.schemas import (
    DepartmentListItem,
    DepartmentListResponse,
)

router = APIRouter()


@router.get(
    "/",
    response_model=DepartmentListResponse,
    summary="List all departments",
    description=(
        "Admin-only. Returns all departments ordered by creation date "
        "(newest first), each with its activation status: active, pending, "
        "or disabled."
    ),
    responses={
        401: {"description": "Missing or invalid admin Bearer token."},
        403: {"description": "Caller is not an admin (read_only)."},
    },
)
async def list_departments(
    use_case: ListDepartmentsUseCase = Depends(
        get_list_departments_use_case
    ),
    _: AdminUser = Depends(require_admin),
) -> DepartmentListResponse:
    orgs = await use_case.execute()
    return DepartmentListResponse(
        departments=[
            DepartmentListItem(
                id=o.id,
                name=o.name,
                status=o.status,
                created_at=o.created_at,
            )
            for o in orgs
        ],
        total=len(orgs),
    )
