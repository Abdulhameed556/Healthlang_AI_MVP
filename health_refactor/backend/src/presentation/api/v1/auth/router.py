"""FastAPI router for auth."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.auth.endpoints.google_oauth import router as google_oauth_router
from backend.src.presentation.api.v1.auth.endpoints.login import router as login_router
from backend.src.presentation.api.v1.auth.endpoints.logout import router as logout_router
from backend.src.presentation.api.v1.auth.endpoints.password_reset import (
    router as password_reset_router,
)

router = APIRouter(prefix="/auth", tags=["auth"])

router.include_router(login_router)
router.include_router(google_oauth_router)
router.include_router(password_reset_router)
router.include_router(logout_router)
