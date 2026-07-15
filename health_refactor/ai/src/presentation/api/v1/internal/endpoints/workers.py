"""Endpoint handler: trigger background worker test task (dev/ops smoke test)."""
from fastapi import APIRouter, HTTPException, status

from ai.src.infrastructure.workers.enqueue import enqueue_test_task
from ai.src.presentation.api.v1.internal.schemas import (
    TriggerTestTaskRequest,
    TriggerTestTaskResponse,
)

router = APIRouter()


@router.post(
    "/workers/test",
    summary="Trigger worker smoke-test task",
    description=(
        "Enqueues the `test_task` Dramatiq job to verify the worker pipeline "
        "(enqueue -> Redis -> worker) is wired correctly. The worker logs the "
        "received payload. Requires Redis and a running worker (`make worker`)."
    ),
    response_model=TriggerTestTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_test_task(body: TriggerTestTaskRequest) -> TriggerTestTaskResponse:
    try:
        payload = enqueue_test_task(message=body.message)
    except Exception as exc:  # broker/Redis unavailable
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to enqueue task — worker broker (Redis) is unavailable.",
        ) from exc

    return TriggerTestTaskResponse(
        enqueued=True,
        task="test_task",
        message=payload.message,
        enqueued_at_iso=payload.enqueued_at_iso,
    )
