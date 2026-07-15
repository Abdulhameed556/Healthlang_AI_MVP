"""FastAPI router for lab orders."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.lab_orders.endpoints.create import (
    router as create_router,
)
from backend.src.presentation.api.v1.lab_orders.endpoints.fulfill import (
    router as fulfill_router,
)
from backend.src.presentation.api.v1.lab_orders.endpoints.list import router as list_router

router = APIRouter(prefix="/lab-orders", tags=["lab-orders"])
router.include_router(create_router)
router.include_router(fulfill_router)
router.include_router(list_router)
