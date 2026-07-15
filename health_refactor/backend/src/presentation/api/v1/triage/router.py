"""FastAPI router for triage."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.triage.endpoints.detail import router as detail_router
from backend.src.presentation.api.v1.triage.endpoints.record import router as record_router

router = APIRouter(prefix="/triage", tags=["triage"])
router.include_router(record_router)
router.include_router(detail_router)
