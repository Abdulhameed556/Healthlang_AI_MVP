"""FastAPI router for retrieval evaluation."""
from fastapi import APIRouter

from ai.src.presentation.api.v1.retrieval_evaluation.endpoints.run import (
    router as run_router,
)
from ai.src.presentation.api.v1.retrieval_evaluation.endpoints.status import (
    router as status_router,
)

router = APIRouter(
    prefix="/retrieval-evaluation",
    tags=["retrieval-evaluation"],
)
router.include_router(run_router)
router.include_router(status_router)
