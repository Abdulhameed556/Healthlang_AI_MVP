"""Public invitation routes (token in path; no JWT)."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.invitations.endpoints.decline_invitation import (
    router as decline_invitation_router,
)

router = APIRouter(prefix="/invitations", tags=["invitations"])

router.include_router(decline_invitation_router)
