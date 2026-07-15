"""Endpoint: list the audit log, scoped by the caller's role."""
from fastapi import APIRouter, Depends, Query, status

from backend.src.application.audit.commands.list_audit_log import ListAuditLogCommand
from backend.src.application.audit.dependencies import get_list_audit_log
from backend.src.application.audit.use_cases.list_audit_log import ListAuditLog
from backend.src.application.auth.context import AuthContext
from backend.src.core.pagination import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from backend.src.presentation.api.v1.audit.schemas import ListAuditLogResponse
from backend.src.presentation.dependencies.auth import require_org_inviter
from backend.src.presentation.openapi import ERROR_JWT, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success

router = APIRouter()


@router.get(
    "/",
    summary="List the audit log",
    description=(
        "`super_admin` sees every department's entries; `admin` sees only their own "
        "department's. No other role may reach this route."
    ),
    response_model=ApiResponse[ListAuditLogResponse],
    status_code=status.HTTP_200_OK,
    responses=envelope_responses(
        ListAuditLogResponse,
        success_message="Audit log retrieved successfully",
        errors=ERROR_JWT,
    ),
)
async def list_audit_log(
    auth: AuthContext = Depends(require_org_inviter),
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    use_case: ListAuditLog = Depends(get_list_audit_log),
) -> ApiResponse[ListAuditLogResponse]:
    result = await use_case.execute(
        ListAuditLogCommand(
            viewer_role=auth.role,
            viewer_department_id=auth.department_id,
            page=page,
            page_size=page_size,
        )
    )
    return success(
        ListAuditLogResponse.model_validate(result),
        message="Audit log retrieved successfully",
        status_code=status.HTTP_200_OK,
    )
