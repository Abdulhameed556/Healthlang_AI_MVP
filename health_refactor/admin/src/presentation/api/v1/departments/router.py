"""FastAPI router for departments."""
from fastapi import APIRouter

from admin.src.presentation.api.v1.departments.endpoints.detail import (
    router as detail_router,
)
from admin.src.presentation.api.v1.departments.endpoints.invitations import (
    router as invitations_router,
)
from admin.src.presentation.api.v1.departments.endpoints.list import (
    router as list_router,
)

router = APIRouter(prefix="/departments", tags=["departments"])
router.include_router(invitations_router)
router.include_router(list_router)
router.include_router(detail_router)
