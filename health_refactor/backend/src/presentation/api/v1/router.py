"""Register all v1 sub-routers."""
from fastapi import APIRouter

from backend.src.presentation.openapi import envelope_responses
from backend.src.presentation.schemas.api_response import ApiResponse, success
from backend.src.presentation.schemas.common import HealthData

from backend.src.presentation.api.v1.audit.router import router as audit_router
from backend.src.presentation.api.v1.auth.router import router as auth_router
from backend.src.presentation.api.v1.break_glass.router import router as break_glass_router
from backend.src.presentation.api.v1.clinical_notes.router import (
    router as clinical_notes_router,
)
from backend.src.presentation.api.v1.dashboard.router import router as dashboard_router
from backend.src.presentation.api.v1.encounters.router import router as encounters_router
from backend.src.presentation.api.v1.inventory.router import router as inventory_router
from backend.src.presentation.api.v1.invitations.router import router as invitations_router
from backend.src.presentation.api.v1.internal.admin.router import router as internal_admin_router
from backend.src.presentation.api.v1.departments.router import router as departments_router
from backend.src.presentation.api.v1.lab_orders.router import router as lab_orders_router
from backend.src.presentation.api.v1.patients.router import router as patients_router
from backend.src.presentation.api.v1.prescriptions.router import (
    router as prescriptions_router,
)
from backend.src.presentation.api.v1.triage.router import router as triage_router
from backend.src.presentation.api.v1.users.router import router as users_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(invitations_router)
v1_router.include_router(users_router)
v1_router.include_router(departments_router)
v1_router.include_router(patients_router)
v1_router.include_router(encounters_router)
v1_router.include_router(triage_router)
v1_router.include_router(clinical_notes_router)
v1_router.include_router(lab_orders_router)
v1_router.include_router(prescriptions_router)
v1_router.include_router(inventory_router)
v1_router.include_router(audit_router)
v1_router.include_router(break_glass_router)
v1_router.include_router(dashboard_router)
v1_router.include_router(internal_admin_router)


@v1_router.get(
    "/health",
    tags=["health"],
    summary="API health check",
    description="Public liveness probe; no authentication required.",
    response_model=ApiResponse[HealthData],
    responses=envelope_responses(HealthData, success_message="OK", errors=()),
)
async def health() -> ApiResponse[HealthData]:
    return success(HealthData(status="ok"), message="OK")
