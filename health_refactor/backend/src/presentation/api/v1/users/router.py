"""FastAPI router for users."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.users.endpoints.list_user_departments import (
    router as list_user_departments_router,
)
from backend.src.presentation.api.v1.users.endpoints.me import router as me_router

router = APIRouter(prefix="/users", tags=["users"])
router.include_router(me_router)
router.include_router(list_user_departments_router)
