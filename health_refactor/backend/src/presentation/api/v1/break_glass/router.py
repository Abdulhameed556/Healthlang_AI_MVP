"""FastAPI router for break-glass access."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.break_glass.endpoints.list import router as list_router
from backend.src.presentation.api.v1.break_glass.endpoints.request import (
    router as request_router,
)
from backend.src.presentation.api.v1.break_glass.endpoints.review import (
    router as review_router,
)

router = APIRouter(prefix="/break-glass", tags=["break-glass"])
router.include_router(request_router)
router.include_router(list_router)
router.include_router(review_router)
