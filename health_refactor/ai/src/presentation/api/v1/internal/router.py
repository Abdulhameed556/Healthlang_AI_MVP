"""FastAPI router for internal."""
from fastapi import APIRouter

from ai.src.presentation.api.v1.internal.endpoints.workers import router as workers_router

router = APIRouter(prefix="/internal", tags=["internal"])
router.include_router(workers_router)
