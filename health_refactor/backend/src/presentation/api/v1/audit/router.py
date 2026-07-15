"""FastAPI router for the audit log."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.audit.endpoints.list import router as list_router

router = APIRouter(prefix="/audit-log", tags=["audit-log"])
router.include_router(list_router)
