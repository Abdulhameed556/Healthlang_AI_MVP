"""FastAPI router for prescriptions."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.prescriptions.endpoints.create import (
    router as create_router,
)
from backend.src.presentation.api.v1.prescriptions.endpoints.dispense import (
    router as dispense_router,
)
from backend.src.presentation.api.v1.prescriptions.endpoints.list import router as list_router

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])
router.include_router(create_router)
router.include_router(dispense_router)
router.include_router(list_router)
