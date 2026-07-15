"""FastAPI router for encounters."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.encounters.endpoints.check_in import (
    router as check_in_router,
)
from backend.src.presentation.api.v1.encounters.endpoints.discharge import (
    router as discharge_router,
)
from backend.src.presentation.api.v1.encounters.endpoints.mark_fulfilled import (
    router as mark_fulfilled_router,
)
from backend.src.presentation.api.v1.encounters.endpoints.queue import router as queue_router
from backend.src.presentation.api.v1.encounters.endpoints.detail import router as detail_router

router = APIRouter(prefix="/encounters", tags=["encounters"])
router.include_router(check_in_router)
router.include_router(queue_router)
router.include_router(mark_fulfilled_router)
router.include_router(discharge_router)
router.include_router(detail_router)
