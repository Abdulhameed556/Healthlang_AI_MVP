"""FastAPI router for clinical notes."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.clinical_notes.endpoints.create import (
    router as create_router,
)
from backend.src.presentation.api.v1.clinical_notes.endpoints.list import router as list_router

router = APIRouter(prefix="/clinical-notes", tags=["clinical-notes"])
router.include_router(create_router)
router.include_router(list_router)
