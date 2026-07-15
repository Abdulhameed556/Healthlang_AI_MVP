"""FastAPI router for auth."""
from fastapi import APIRouter

from admin.src.presentation.api.v1.auth.endpoints.accept_invitation import (
    router as accept_invitation_router,
)
from admin.src.presentation.api.v1.auth.endpoints.login import router as login_router
from admin.src.presentation.api.v1.auth.endpoints.logout import (
    router as logout_router,
)

router = APIRouter(prefix="/auth", tags=["auth"])
router.include_router(login_router)
router.include_router(logout_router)
router.include_router(accept_invitation_router)
