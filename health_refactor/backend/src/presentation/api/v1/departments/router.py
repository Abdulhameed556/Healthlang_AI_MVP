"""FastAPI router for departments."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.departments.endpoints.invite import router as invite_router
from backend.src.presentation.api.v1.departments.endpoints.me import router as me_router
from backend.src.presentation.api.v1.departments.endpoints.users import router as users_router

router = APIRouter(prefix="/departments", tags=["departments"])
router.include_router(me_router)
router.include_router(users_router)
router.include_router(invite_router)
