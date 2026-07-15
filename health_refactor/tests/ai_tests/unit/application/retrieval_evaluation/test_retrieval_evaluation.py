"""Unit tests: ai/src/application/retrieval_evaluation/* (steps + pipeline)."""
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

_AGENT_ID = UUID("dddddddd-dddd-dddd-dddd-dddddddddddd")
_KB_ENTRY_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _make_ctx(**overrides):
    from ai.src.application.retrieval_evaluation.context import (
        RetrievalEvaluationContext,
    )

    defaults = dict(run_id="run-1", agent_id=_AGENT_ID, kb_entry_id=_KB_ENTRY_ID)
    return RetrievalEvaluationContext(**{**defaults, **overrides})


def _golden(q="Q?", a="A."):
    from ai.src.domain.retrieval_evaluation.entities import RetrievalGolden

    return RetrievalGolden(question=q, expected_output=a, source_context=["c"])


def _metric(name="contextual_relevancy", score=0.9):
    from ai.src.domain.retrieval_evaluation.entities import MetricResult

    return MetricResult(name=name, score=score, threshold=0.7, success=True)


def _session_factory(mock_session):
    ctx_mgr = AsyncMock(
        __aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()
    )
    return MagicMock(return_value=ctx_mgr)


# ── _group_chunks ─────────────────────────────────────────────────────────────


def test_group_chunks_respects_size_and_max() -> None:
    from ai.src.application.retrieval_evaluation.steps.synthesize_testset import (
        _group_chunks,
    )

    chunks = [f"c{i}" for i in range(10)]
    groups = _group_chunks(chunks, per_group=2, max_groups=3)
    assert groups == [["c0", "c1"], ["c2", "c3"], ["c4", "c5"]]


# ── LoadSourceChunksStep ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_source_chunks_step(monkeypatch) -> None:
    from ai.src.application.retrieval_evaluation.steps import load_source_chunks as mod

    entry = MagicMock(storage_path="orgs/o/doc.txt", file_type="txt")
    session = AsyncMock()
    session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=entry)
    )

    monkeypatch.setattr(mod, "download_file", AsyncMock(return_value=b"raw"))
    parser = MagicMock()
    parser.parse.return_value = "full text"
    parser_factory = MagicMock()
    parser_factory.get_parser.return_value = parser
    chunker = MagicMock()
    chunker.chunk.return_value = ["chunk a", "chunk b"]

    step = mod.LoadSourceChunksStep(
        _session_factory(session), parser_factory, chunker
    )
    ctx = _make_ctx()
    await step.run(ctx)

    assert ctx.storage_path == "orgs/o/doc.txt"
    assert ctx.file_type == "txt"
    assert ctx.source_chunks == ["chunk a", "chunk b"]
    parser_factory.get_parser.assert_called_once_with("txt")


# ── SynthesizeTestsetStep ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_synthesize_testset_step_calls_synthesizer() -> None:
    from ai.src.application.retrieval_evaluation.steps.synthesize_testset import (
        SynthesizeTestsetStep,
    )

    synthesizer = AsyncMock()
    synthesizer.synthesize.return_value = [_golden()]

    ctx = _make_ctx(
        source_chunks=["c0", "c1", "c2"],
        chunks_per_context=2,
        max_contexts=4,
        max_goldens_per_context=2,
    )
    await SynthesizeTestsetStep(synthesizer).run(ctx)

    synthesizer.synthesize.assert_called_once_with([["c0", "c1"], ["c2"]], 2)
    assert ctx.goldens == [_golden()]


# ── RunTestCasesStep ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_test_cases_step_builds_question_results() -> None:
    from ai.src.application.retrieval_evaluation.steps.run_test_cases import (
        RunTestCasesStep,
    )

    retrieval = AsyncMock()
    retrieval.retrieve.return_value = [
        MagicMock(text="chunk-1"),
        MagicMock(text="chunk-2"),
    ]
    scorer = AsyncMock()
    scorer.score.return_value = [_metric()]

    ctx = _make_ctx(goldens=[_golden("Q1?", "A1")], top_k=3)
    await RunTestCasesStep(retrieval, scorer).run(ctx)

    retrieval.retrieve.assert_called_once_with("Q1?", _AGENT_ID, 3, kb_entry_id=_KB_ENTRY_ID)
    assert len(ctx.question_results) == 1
    qr = ctx.question_results[0]
    assert qr.retrieved_context == ["chunk-1", "chunk-2"]
    assert qr.metrics[0].name == "contextual_relevancy"


# ── _aggregate ────────────────────────────────────────────────────────────────


def test_aggregate_computes_mean_per_metric() -> None:
    from ai.src.application.retrieval_evaluation.pipeline import _aggregate
    from ai.src.domain.retrieval_evaluation.entities import QuestionResult

    q1 = QuestionResult("q1", "e", [], [_metric("faith", 0.8), _metric("rel", 0.6)])
    q2 = QuestionResult("q2", "e", [], [_metric("faith", 0.4), _metric("rel", 1.0)])
    agg = _aggregate([q1, q2])

    assert agg["faith"] == pytest.approx(0.6)
    assert agg["rel"] == pytest.approx(0.8)


def test_aggregate_empty_is_empty() -> None:
    from ai.src.application.retrieval_evaluation.pipeline import _aggregate

    assert _aggregate([]) == {}


# ── RetrievalEvaluationPipeline ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_completes_and_aggregates() -> None:
    from ai.src.application.retrieval_evaluation.pipeline import (
        RetrievalEvaluationPipeline,
    )
    from ai.src.domain.retrieval_evaluation.entities import QuestionResult, RunStatus

    async def _run(ctx):
        ctx.question_results = [
            QuestionResult("q", "e", [], [_metric("faith", 0.9)])
        ]

    step = MagicMock()
    step.run = AsyncMock(side_effect=_run)
    store = AsyncMock()

    pipeline = RetrievalEvaluationPipeline([step], store)
    report = await pipeline.run(_make_ctx())

    assert report.status == RunStatus.COMPLETED
    assert report.aggregate_scores["faith"] == pytest.approx(0.9)
    # saved twice: RUNNING then COMPLETED
    assert store.save.await_count == 2


@pytest.mark.asyncio
async def test_pipeline_marks_failed_on_step_error() -> None:
    from ai.src.application.retrieval_evaluation.pipeline import (
        RetrievalEvaluationPipeline,
    )
    from ai.src.domain.retrieval_evaluation.entities import RunStatus

    step = MagicMock()
    step.run = AsyncMock(side_effect=RuntimeError("synth failed"))
    store = AsyncMock()

    pipeline = RetrievalEvaluationPipeline([step], store)
    report = await pipeline.run(_make_ctx())

    assert report.status == RunStatus.FAILED
    assert "synth failed" in report.error
    assert store.save.await_count == 2
