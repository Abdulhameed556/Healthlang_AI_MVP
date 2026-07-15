"""Endpoint: trigger or list chat evaluation runs."""
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.application.chat_evaluation.dependencies import (
    build_chat_evaluation_pipeline,
)
from ai.src.domain.chat_evaluation.entities import (
    ChatEvalReport,
    EvalMode,
    RunStatus,
)
from ai.src.infrastructure.chat_evaluation.dataset_store import (
    get_dataset_store,
)
from ai.src.infrastructure.chat_evaluation.run_store import get_run_store
from ai.src.presentation.api.v1.chat_evaluation.schemas import (
    ListRunsResponse,
    RunChatEvaluationRequest,
    RunChatEvaluationResponse,
    RunSummaryResponse,
)

router = APIRouter()

_AGENT_REQUIRED_MODES = {
    EvalMode.SCENARIO,
    EvalMode.E2E,
    EvalMode.CONVERSATION,
}

_CASES_AUTO_MODES = {EvalMode.CONVERSATION}

_VALID_MODES = {
    EvalMode.INPUT_GUARDRAIL,
    EvalMode.SCENARIO,
    EvalMode.OUTPUT_GUARDRAIL,
    EvalMode.E2E,
    EvalMode.CONVERSATION,
}

_RUN_DESCRIPTION = (
    "Triggers a chat evaluation run for the given eval_mode. "
    "Supply test cases via dataset_id (from POST /datasets) or inline "
    "test_cases. For conversation mode, cases are auto-generated from "
    "the agent's configured scenarios — only agent_id is required.\n\n"
    "Returns immediately with run_id and status='pending'. "
    "Poll GET /status/{run_id} for progress and results.\n\n"
    "**Modes and required fields:**\n"
    "- input_guardrail — each case: `{query, should_block, rules?}`\n"
    "- output_guardrail — each case: "
    "`{query, assistant_message, expected_action, rules?}`\n"
    "- scenario — each case: `{query, expected_scenario_ids?}`; "
    "agent_id required\n"
    "- e2e — each case: `{query, expected_answer}`; agent_id required\n"
    "- conversation — no test_cases needed; agent_id required; "
    "optionally set determinism_runs (1–5), conversation_rounds (2–10), "
    "conversation_source ('synthetic'|'real'), sample_size (1–50)"
)


async def _execute_run(
    run_id: str,
    eval_mode: str,
    agent_id: str | None,
    test_cases: list,
    determinism_runs: int,
    conversation_rounds: int,
    conversation_source: str,
    sample_size: int,
    first_speaker: str,
    welcome_message: str,
    agent_variables: dict,
    api_tool_mocks: dict,
    judge_criteria: list,
    max_minutes: int,
) -> None:
    ctx = ChatEvalContext(
        run_id=run_id,
        eval_mode=eval_mode,
        test_cases=test_cases,
        agent_id=agent_id,
        determinism_runs=determinism_runs,
        conversation_rounds=conversation_rounds,
        conversation_source=conversation_source,
        sample_size=sample_size,
        first_speaker=first_speaker,
        welcome_message=welcome_message,
        agent_variables=agent_variables,
        api_tool_mocks=api_tool_mocks,
        judge_criteria=judge_criteria,
        max_minutes=max_minutes,
    )
    pipeline = build_chat_evaluation_pipeline(
        eval_mode, conversation_source=conversation_source
    )
    await pipeline.run(ctx)


@router.post(
    "",
    summary="Start a chat evaluation run",
    description=_RUN_DESCRIPTION,
    response_description=(
        "Evaluation run queued. Poll /status/{run_id} for progress."
    ),
    response_model=RunChatEvaluationResponse,
    status_code=202,
)
async def run_evaluation(
    payload: RunChatEvaluationRequest,
    background_tasks: BackgroundTasks,
) -> RunChatEvaluationResponse:
    if payload.eval_mode not in _VALID_MODES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid eval_mode '{payload.eval_mode}'. "
                f"Must be one of: {sorted(_VALID_MODES)}"
            ),
        )

    if (
        payload.eval_mode in _AGENT_REQUIRED_MODES
        and payload.agent_id is None
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                f"agent_id is required for "
                f"eval_mode='{payload.eval_mode}'"
            ),
        )

    if payload.eval_mode not in _CASES_AUTO_MODES:
        if payload.dataset_id is None and payload.test_cases is None:
            raise HTTPException(
                status_code=422,
                detail="Provide either dataset_id or test_cases.",
            )
        if (
            payload.dataset_id is not None
            and payload.test_cases is not None
        ):
            raise HTTPException(
                status_code=422,
                detail="Provide dataset_id or test_cases, not both.",
            )

    if payload.eval_mode in _CASES_AUTO_MODES:
        test_cases: list = []
    elif payload.dataset_id is not None:
        dataset = await get_dataset_store().get(payload.dataset_id)
        if dataset is None:
            raise HTTPException(
                status_code=404, detail="dataset not found"
            )
        test_cases = dataset.test_cases
    else:
        test_cases = payload.test_cases or []

    run_id = str(uuid4())
    agent_id = str(payload.agent_id) if payload.agent_id else None
    created_at = datetime.now(timezone.utc).isoformat()

    await get_run_store().save(
        ChatEvalReport(
            run_id=run_id,
            eval_mode=payload.eval_mode,
            agent_id=agent_id,
            status=RunStatus.PENDING,
            created_at=created_at,
        )
    )
    background_tasks.add_task(
        _execute_run,
        run_id,
        payload.eval_mode,
        agent_id,
        test_cases,
        payload.determinism_runs,
        payload.conversation_rounds,
        payload.conversation_source,
        payload.sample_size,
        payload.first_speaker,
        payload.welcome_message,
        dict(payload.agent_variables),
        dict(payload.api_tool_mocks),
        list(payload.judge_criteria),
        payload.max_minutes,
    )
    return RunChatEvaluationResponse(
        run_id=run_id, status=RunStatus.PENDING
    )


@router.get(
    "",
    summary="List evaluation runs for an agent",
    description=(
        "Returns a paginated summary list of past evaluation runs for the "
        "given agent, newest first. Only aggregate-level data is returned — "
        "use GET /status/{run_id} to fetch full case results."
    ),
    response_model=ListRunsResponse,
)
async def list_runs(
    agent_id: str | None = Query(
        default=None,
        description="Filter by agent UUID. Omit to list across all agents.",
    ),
    page: int = Query(
        default=1,
        ge=1,
        description="Page number (1-based).",
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Number of runs per page (1–100).",
    ),
) -> ListRunsResponse:
    runs, total = await get_run_store().list(agent_id, page, page_size)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ListRunsResponse(
        runs=[
            RunSummaryResponse(
                run_id=r.run_id,
                eval_mode=r.eval_mode,
                agent_id=r.agent_id,
                status=r.status,
                created_at=r.created_at,
                aggregate_scores=r.aggregate_scores,
                error=r.error,
            )
            for r in runs
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
