"""Unit tests: ai/src/presentation/api/v1/retrieval_evaluation/* (batch API)."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

_AGENT_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_ENTRY_ID_1 = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_ENTRY_ID_2 = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def _make_entry_report(kb_entry_id=_ENTRY_ID_1, status="COMPLETED", score=0.9):
    from ai.src.domain.retrieval_evaluation.entities import (
        EvaluationReport,
        MetricResult,
        QuestionResult,
        RunStatus,
    )

    return EvaluationReport(
        run_id="r1",
        agent_id=_AGENT_ID,
        kb_entry_id=kb_entry_id,
        status=RunStatus.COMPLETED if status == "COMPLETED" else RunStatus.FAILED,
        question_results=[
            QuestionResult(
                question="Q?",
                expected_output="E",
                retrieved_context=["c1"],
                metrics=[MetricResult("contextual_relevancy", score, 0.7, True, "ok")],
            )
        ],
        aggregate_scores={"contextual_relevancy": score},
    )


def _make_batch_report(status="PENDING"):
    from ai.src.domain.retrieval_evaluation.entities import BatchEvaluationReport, RunStatus

    return BatchEvaluationReport(
        run_id="run-1",
        agent_id=_AGENT_ID,
        kb_entry_ids=[_ENTRY_ID_1, _ENTRY_ID_2],
        status=getattr(RunStatus, status),
    )


# ── BatchEvaluationReportResponse.from_domain ─────────────────────────────────


def test_batch_report_response_from_domain_maps_entry_reports() -> None:
    from ai.src.domain.retrieval_evaluation.entities import BatchEvaluationReport, RunStatus
    from ai.src.presentation.api.v1.retrieval_evaluation.schemas import (
        BatchEvaluationReportResponse,
    )

    batch = BatchEvaluationReport(
        run_id="r1",
        agent_id=_AGENT_ID,
        kb_entry_ids=[_ENTRY_ID_1, _ENTRY_ID_2],
        status=RunStatus.COMPLETED,
        entry_reports=[_make_entry_report(_ENTRY_ID_1), _make_entry_report(_ENTRY_ID_2)],
        aggregate_scores={"contextual_relevancy": 0.9},
    )
    schema = BatchEvaluationReportResponse.from_domain(batch)

    assert schema.run_id == "r1"
    assert schema.status == "completed"
    assert len(schema.entry_reports) == 2
    assert schema.entry_reports[0].kb_entry_id == _ENTRY_ID_1
    assert schema.aggregate_scores["contextual_relevancy"] == pytest.approx(0.9)


# ── _merge_aggregate_scores ───────────────────────────────────────────────────


def test_merge_aggregate_scores_averages_across_entries() -> None:
    from ai.src.presentation.api.v1.retrieval_evaluation.endpoints.run import (
        _merge_aggregate_scores,
    )

    r1 = _make_entry_report(_ENTRY_ID_1, score=0.8)
    r2 = _make_entry_report(_ENTRY_ID_2, score=0.4)
    agg = _merge_aggregate_scores([r1, r2])

    assert agg["contextual_relevancy"] == pytest.approx(0.6)


def test_merge_aggregate_scores_skips_failed_entries() -> None:
    from ai.src.domain.retrieval_evaluation.entities import EvaluationReport, RunStatus
    from ai.src.presentation.api.v1.retrieval_evaluation.endpoints.run import (
        _merge_aggregate_scores,
    )

    good = _make_entry_report(_ENTRY_ID_1, score=1.0)
    failed = EvaluationReport(
        run_id="",
        agent_id=_AGENT_ID,
        kb_entry_id=_ENTRY_ID_2,
        status=RunStatus.FAILED,
        error="boom",
    )
    agg = _merge_aggregate_scores([good, failed])

    assert agg["contextual_relevancy"] == pytest.approx(1.0)


# ── run endpoint ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_endpoint_saves_pending_batch_and_schedules_task() -> None:
    from ai.src.presentation.api.v1.retrieval_evaluation.endpoints import run as mod
    from ai.src.presentation.api.v1.retrieval_evaluation.schemas import RunEvaluationRequest

    background = MagicMock()
    store = AsyncMock()
    payload = RunEvaluationRequest(
        agent_id=_AGENT_ID, kb_entry_ids=[_ENTRY_ID_1, _ENTRY_ID_2]
    )

    with patch.object(mod, "get_run_store", return_value=store):
        resp = await mod.run_evaluation(payload, background)

    assert resp.status == "pending"
    assert resp.run_id
    store.save.assert_awaited_once()
    background.add_task.assert_called_once()


@pytest.mark.asyncio
async def test_run_one_builds_context_and_runs_pipeline() -> None:
    from ai.src.presentation.api.v1.retrieval_evaluation.endpoints import run as mod

    pipeline = MagicMock()
    pipeline.run = AsyncMock(return_value=_make_entry_report())

    with patch.object(mod, "build_retrieval_evaluation_pipeline", return_value=pipeline):
        result = await mod._run_one(
            agent_id=_AGENT_ID,
            kb_entry_id=_ENTRY_ID_1,
            top_k=5,
            max_contexts=4,
            max_goldens_per_context=2,
        )

    pipeline.run.assert_awaited_once()
    ctx_arg = pipeline.run.call_args[0][0]
    assert ctx_arg.agent_id == _AGENT_ID
    assert ctx_arg.kb_entry_id == _ENTRY_ID_1
    assert result.status == "completed"


@pytest.mark.asyncio
async def test_execute_batch_completes_all_entries() -> None:
    from ai.src.presentation.api.v1.retrieval_evaluation.endpoints import run as mod

    store = AsyncMock()
    store.get.return_value = _make_batch_report("PENDING")

    with patch.object(mod, "get_run_store", return_value=store), patch.object(
        mod, "_run_one", AsyncMock(return_value=_make_entry_report())
    ):
        await mod._execute_batch(
            run_id="run-1",
            agent_id=_AGENT_ID,
            kb_entry_ids=[_ENTRY_ID_1, _ENTRY_ID_2],
            top_k=5,
            max_contexts=4,
            max_goldens_per_context=2,
        )

    # saved twice: RUNNING then final state
    assert store.save.await_count == 2
    final_batch = store.save.call_args_list[-1][0][0]
    assert final_batch.status == "completed"
    assert len(final_batch.entry_reports) == 2


# ── status endpoint ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_status_endpoint_returns_batch_report() -> None:
    from ai.src.domain.retrieval_evaluation.entities import BatchEvaluationReport, RunStatus
    from ai.src.presentation.api.v1.retrieval_evaluation.endpoints import status as mod

    batch = BatchEvaluationReport(
        run_id="r1",
        agent_id=_AGENT_ID,
        kb_entry_ids=[_ENTRY_ID_1],
        status=RunStatus.COMPLETED,
    )
    store = AsyncMock()
    store.get.return_value = batch

    with patch.object(mod, "get_run_store", return_value=store):
        resp = await mod.get_evaluation_status("r1")

    assert resp.run_id == "r1"
    assert resp.status == "completed"
    assert resp.kb_entry_ids == [_ENTRY_ID_1]


@pytest.mark.asyncio
async def test_status_endpoint_404_when_missing() -> None:
    from fastapi import HTTPException

    from ai.src.presentation.api.v1.retrieval_evaluation.endpoints import status as mod

    store = AsyncMock()
    store.get.return_value = None

    with patch.object(mod, "get_run_store", return_value=store):
        with pytest.raises(HTTPException) as exc:
            await mod.get_evaluation_status("missing")

    assert exc.value.status_code == 404
