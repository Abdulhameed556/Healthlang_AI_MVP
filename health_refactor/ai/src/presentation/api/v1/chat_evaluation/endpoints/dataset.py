"""Endpoint: upload a test-case dataset for later use in a run."""
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from ai.src.domain.chat_evaluation.entities import ChatEvalDataset, EvalMode
from ai.src.infrastructure.chat_evaluation.dataset_store import get_dataset_store
from ai.src.presentation.api.v1.chat_evaluation.schemas import (
    UploadDatasetRequest,
    UploadDatasetResponse,
)

router = APIRouter()

_VALID_MODES = {EvalMode.INPUT_GUARDRAIL, EvalMode.SCENARIO, EvalMode.OUTPUT_GUARDRAIL, EvalMode.E2E}


@router.post(
    "",
    summary="Upload a chat evaluation dataset",
    description=(
        "Stores a named collection of test cases for a specific eval_mode. "
        "Returns a dataset_id you can reference in POST /runs. "
        "Datasets are held in memory for the lifetime of the server process."
    ),
    response_description="Dataset stored. Use dataset_id in POST /runs.",
    response_model=UploadDatasetResponse,
    status_code=201,
)
async def upload_dataset(payload: UploadDatasetRequest) -> UploadDatasetResponse:
    if payload.eval_mode not in _VALID_MODES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid eval_mode '{payload.eval_mode}'. "
                f"Must be one of: {sorted(_VALID_MODES)}"
            ),
        )
    dataset_id = f"dataset-{payload.eval_mode}-{uuid4().hex[:8]}"
    dataset = ChatEvalDataset(
        dataset_id=dataset_id,
        eval_mode=payload.eval_mode,
        test_cases=payload.test_cases,
    )
    await get_dataset_store().save(dataset)
    return UploadDatasetResponse(
        dataset_id=dataset_id,
        eval_mode=payload.eval_mode,
        case_count=len(payload.test_cases),
    )
