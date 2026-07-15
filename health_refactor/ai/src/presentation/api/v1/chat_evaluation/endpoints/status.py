"""Endpoint: poll status and results of a chat evaluation run."""
from fastapi import APIRouter, HTTPException

from ai.src.infrastructure.chat_evaluation.run_store import get_run_store
from ai.src.presentation.api.v1.chat_evaluation.schemas import ChatEvalReportResponse

router = APIRouter()


@router.get(
    "/{run_id}",
    summary="Get chat evaluation run status and results",
    description=(
        "Returns the current status and full results of a chat evaluation run. "
        "Status progresses: pending → running → completed | failed. "
        "Results (case_results, aggregate_scores) are populated once status is 'completed'."
    ),
    response_description="Chat evaluation report with current status and per-case results.",
    response_model=ChatEvalReportResponse,
)
async def get_run_status(run_id: str) -> ChatEvalReportResponse:
    report = await get_run_store().get(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="evaluation run not found")
    return ChatEvalReportResponse.from_domain(report)
