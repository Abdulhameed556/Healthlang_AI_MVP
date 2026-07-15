"""Endpoint: start a batch retrieval-evaluation run."""
import asyncio
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks

from ai.src.application.retrieval_evaluation.context import RetrievalEvaluationContext
from ai.src.application.retrieval_evaluation.dependencies import (
    build_retrieval_evaluation_pipeline,
)
from ai.src.domain.retrieval_evaluation.entities import (
    BatchEvaluationReport,
    EvaluationReport,
    RunStatus,
)
from ai.src.infrastructure.retrieval_evaluation.run_store import get_run_store
from ai.src.presentation.api.v1.retrieval_evaluation.schemas import (
    RunEvaluationRequest,
    RunEvaluationResponse,
)

router = APIRouter()


def _merge_aggregate_scores(
    entry_reports: list[EvaluationReport],
) -> dict[str, float]:
    """Mean of per-entry aggregate scores across all completed entries."""
    totals: dict[str, float] = {}
    counts: dict[str, int] = {}
    for er in entry_reports:
        for metric, score in er.aggregate_scores.items():
            totals[metric] = totals.get(metric, 0.0) + score
            counts[metric] = counts.get(metric, 0) + 1
    return {m: totals[m] / counts[m] for m in totals if counts[m]}


async def _run_one(
    agent_id: UUID,
    kb_entry_id: UUID,
    top_k: int,
    max_contexts: int,
    max_goldens_per_context: int,
) -> EvaluationReport:
    ctx = RetrievalEvaluationContext(
        run_id=str(uuid4()),
        agent_id=agent_id,
        kb_entry_id=kb_entry_id,
        top_k=top_k,
        max_contexts=max_contexts,
        max_goldens_per_context=max_goldens_per_context,
    )
    pipeline = build_retrieval_evaluation_pipeline()
    return await pipeline.run(ctx)


async def _execute_batch(
    run_id: str,
    agent_id: UUID,
    kb_entry_ids: list[UUID],
    top_k: int,
    max_contexts: int,
    max_goldens_per_context: int,
) -> None:
    store = get_run_store()
    batch = await store.get(run_id)
    batch.status = RunStatus.RUNNING
    await store.save(batch)

    results = await asyncio.gather(
        *[
            _run_one(agent_id, eid, top_k, max_contexts, max_goldens_per_context)
            for eid in kb_entry_ids
        ],
        return_exceptions=True,
    )

    entry_reports: list[EvaluationReport] = []
    for eid, result in zip(kb_entry_ids, results):
        if isinstance(result, Exception):
            entry_reports.append(
                EvaluationReport(
                    run_id="",
                    agent_id=agent_id,
                    kb_entry_id=eid,
                    status=RunStatus.FAILED,
                    error=str(result),
                )
            )
        else:
            entry_reports.append(result)

    all_failed = all(er.status == RunStatus.FAILED for er in entry_reports)
    batch.entry_reports = entry_reports
    batch.aggregate_scores = _merge_aggregate_scores(entry_reports)
    batch.status = RunStatus.FAILED if all_failed else RunStatus.COMPLETED
    await store.save(batch)


@router.post(
    "/run",
    summary="Start a retrieval evaluation batch",
    description=(
        "Queues a batch retrieval-evaluation run for one or more KB entries. "
        "Each entry is evaluated independently in parallel: the pipeline synthesises "
        "test questions from the document, retrieves context via the agent's retrieval "
        "chain, then scores each result with DeepEval RAG metrics "
        "(contextual_relevancy, contextual_precision, contextual_recall). "
        "Returns immediately with a run_id and status='pending'. "
        "Poll GET /status/{run_id} to track progress and retrieve results."
    ),
    response_description="Evaluation run queued. Poll /status/{run_id} for progress.",
    response_model=RunEvaluationResponse,
    status_code=202,
)
async def run_evaluation(
    payload: RunEvaluationRequest, background_tasks: BackgroundTasks
) -> RunEvaluationResponse:
    run_id = str(uuid4())
    await get_run_store().save(
        BatchEvaluationReport(
            run_id=run_id,
            agent_id=payload.agent_id,
            kb_entry_ids=payload.kb_entry_ids,
            status=RunStatus.PENDING,
        )
    )
    background_tasks.add_task(
        _execute_batch,
        run_id,
        payload.agent_id,
        payload.kb_entry_ids,
        payload.top_k,
        payload.max_contexts,
        payload.max_goldens_per_context,
    )
    return RunEvaluationResponse(run_id=run_id, status=RunStatus.PENDING)
