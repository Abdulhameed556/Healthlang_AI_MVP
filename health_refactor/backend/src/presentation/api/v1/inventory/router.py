"""FastAPI router for inventory."""
from fastapi import APIRouter

from backend.src.presentation.api.v1.inventory.endpoints.create import router as create_router
from backend.src.presentation.api.v1.inventory.endpoints.list import router as list_router

router = APIRouter(prefix="/inventory", tags=["inventory"])
router.include_router(create_router)
router.include_router(list_router)
