"""FastAPI router for admin users management."""
from fastapi import APIRouter

from admin.src.presentation.api.v1.users.endpoints.detail import router as detail_router
from admin.src.presentation.api.v1.users.endpoints.edit_role import (
    router as edit_role_router,
)
from admin.src.presentation.api.v1.users.endpoints.invite import router as invite_router
from admin.src.presentation.api.v1.users.endpoints.list import router as list_router
from admin.src.presentation.api.v1.users.endpoints.lock import router as lock_router
from admin.src.presentation.api.v1.users.endpoints.me import router as me_router
from admin.src.presentation.api.v1.users.endpoints.remove import router as remove_router
from admin.src.presentation.api.v1.users.endpoints.resend_invitation import (
    router as resend_invitation_router,
)
from admin.src.presentation.api.v1.users.endpoints.unlock import router as unlock_router

router = APIRouter(prefix="/users", tags=["users"])
router.include_router(me_router)
router.include_router(invite_router)
router.include_router(resend_invitation_router)
router.include_router(list_router)
router.include_router(edit_role_router)
router.include_router(unlock_router)
router.include_router(lock_router)
router.include_router(remove_router)
router.include_router(detail_router)
