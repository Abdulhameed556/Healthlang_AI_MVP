"""Register all v1 sub-routers."""
from fastapi import APIRouter

from admin.src.presentation.api.v1.auth.router import router as auth_router
from admin.src.presentation.api.v1.departments.router import router as departments_router
from admin.src.presentation.api.v1.users.router import router as users_router

v1_router = APIRouter()

v1_router.include_router(auth_router)
v1_router.include_router(users_router)
v1_router.include_router(departments_router)


@v1_router.get("/health", tags=["health"])
async def health() -> dict:
    return {"error": False, "status_code": 200, "message": "OK", "data": {"status": "ok"}}
