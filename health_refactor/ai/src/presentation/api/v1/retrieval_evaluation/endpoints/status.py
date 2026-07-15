"""Endpoint: poll the status/results of a retrieval-evaluation run."""
from fastapi import APIRouter, HTTPException

from ai.src.infrastructure.retrieval_evaluation.run_store import get_run_store
from ai.src.presentation.api.v1.retrieval_evaluation.schemas import (
    BatchEvaluationReportResponse,
)

router = APIRouter()


@router.get(
    "/{run_id}",
    summary="Get evaluation run status and results",
    description=(
        "Returns the current status and full results of a batch retrieval-evaluation run. "
        "Status progresses: pending → running → completed | failed. "
        "Results (entry_reports, aggregate_scores) are populated once status is 'completed'. "
        "Individual entries that fail are reported with status='failed' and an error message; "
        "the batch status is 'failed' only if every entry fails."
    ),
    response_description="Evaluation run report with current status and per-entry results.",
    response_model=BatchEvaluationReportResponse,
)
async def get_evaluation_status(run_id: str) -> BatchEvaluationReportResponse:
    report = await get_run_store().get(run_id)
    if report is None:
        raise HTTPException(status_code=404, detail="evaluation run not found")
    return BatchEvaluationReportResponse.from_domain(report)
