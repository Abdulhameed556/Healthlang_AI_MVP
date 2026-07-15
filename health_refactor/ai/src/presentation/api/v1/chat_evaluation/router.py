"""FastAPI router for chat evaluation."""
from fastapi import APIRouter

from ai.src.presentation.api.v1.chat_evaluation.endpoints import dataset, run, status

router = APIRouter(prefix="/chat-evaluation", tags=["chat-evaluation"])

router.include_router(dataset.router, prefix="/datasets")
router.include_router(run.router, prefix="/runs")
router.include_router(status.router, prefix="/status")
