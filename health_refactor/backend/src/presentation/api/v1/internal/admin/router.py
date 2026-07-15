"""Admin Portal → Backend router (API key required on all routes)."""
from fastapi import APIRouter, Depends

from backend.src.presentation.openapi import ERROR_UNAUTHORIZED, envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success
from backend.src.presentation.schemas.common import HealthData

from backend.src.presentation.api.v1.internal.admin.endpoints.create_invited_user import (
    router as create_invited_user_router,
)
from backend.src.presentation.dependencies.admin_internal import require_admin_api_key

router = APIRouter(
    prefix="/internal/admin",
    tags=["internal-admin"],
    dependencies=[Depends(require_admin_api_key)],
)

router.include_router(create_invited_user_router)


@router.get(
    "/health",
    summary="Internal admin health check",
    description="Confirms API key auth and routing for the Admin Portal integration.",
    response_model=ApiResponse[HealthData],
    responses=envelope_responses(
        HealthData,
        success_message="OK",
        errors=ERROR_UNAUTHORIZED,
    ),
)
async def internal_admin_health() -> ApiResponse[HealthData]:
    return success(HealthData(status="ok"), message="OK")
