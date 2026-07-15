"""FastAPI router for patients."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.patients.endpoints.detail import router as detail_router

router = APIRouter(prefix="/patients", tags=["patients"])
router.include_router(detail_router)
