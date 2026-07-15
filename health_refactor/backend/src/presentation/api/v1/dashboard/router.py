"""FastAPI router for the department dashboard."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.dashboard.endpoints.get import router as get_router

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
router.include_router(get_router)
