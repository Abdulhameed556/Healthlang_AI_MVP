"""Unit tests: ai/src/infrastructure/chat_evaluation/*"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── InMemoryRunStore ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_run_store_save_and_get() -> None:
    from ai.src.domain.chat_evaluation.entities import ChatEvalReport
    from ai.src.infrastructure.chat_evaluation.run_store import InMemoryRunStore

    store = InMemoryRunStore()
    report = ChatEvalReport(run_id="r1", eval_mode="e2e", agent_id=None)
    await store.save(report)

    assert await store.get("r1") is report


@pytest.mark.asyncio
async def test_run_store_get_missing_returns_none() -> None:
    from ai.src.infrastructure.chat_evaluation.run_store import InMemoryRunStore

    store = InMemoryRunStore()
    assert await store.get("nonexistent") is None


@pytest.mark.asyncio
async def test_run_store_save_overwrites() -> None:
    from ai.src.domain.chat_evaluation.entities import ChatEvalReport, RunStatus
    from ai.src.infrastructure.chat_evaluation.run_store import InMemoryRunStore

    store = InMemoryRunStore()
    r = ChatEvalReport(run_id="r1", eval_mode="e2e", agent_id=None)
    await store.save(r)
    r.status = RunStatus.COMPLETED
    await store.save(r)

    assert (await store.get("r1")).status == RunStatus.COMPLETED


def test_get_run_store_returns_singleton() -> None:
    from ai.src.infrastructure.chat_evaluation.run_store import get_run_store

    assert get_run_store() is get_run_store()


@pytest.mark.asyncio
async def test_run_store_list_paginates() -> None:
    from ai.src.domain.chat_evaluation.entities import ChatEvalReport
    from ai.src.infrastructure.chat_evaluation.run_store import InMemoryRunStore

    store = InMemoryRunStore()
    for i in range(3):
        r = ChatEvalReport(run_id=f"list-{i}", eval_mode="e2e", agent_id="ag-1")
        r.created_at = f"2026-01-0{i + 1}T00:00:00"
        await store.save(r)

    page, total = await store.list(agent_id="ag-1", page=1, page_size=2)
    assert total == 3
    assert len(page) == 2


def test_get_run_store_creates_in_memory_when_no_s3(monkeypatch) -> None:
    from ai.src.infrastructure.chat_evaluation import run_store as mod

    monkeypatch.setattr(mod, "_instance", None)
    with patch("ai.src.core.config.settings") as mock_settings:
        mock_settings.aws_s3_bucket = None
        store = mod.get_run_store()

    assert isinstance(store, mod.InMemoryRunStore)
    monkeypatch.setattr(mod, "_instance", None)


# ── InMemoryDatasetStore ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_dataset_store_save_and_get() -> None:
    from ai.src.domain.chat_evaluation.entities import ChatEvalDataset, EvalMode
    from ai.src.infrastructure.chat_evaluation.dataset_store import InMemoryDatasetStore

    store = InMemoryDatasetStore()
    ds = ChatEvalDataset(
        dataset_id="d1", eval_mode=EvalMode.INPUT_GUARDRAIL, test_cases=[{"query": "hi"}]
    )
    await store.save(ds)

    result = await store.get("d1")
    assert result is ds
    assert result.test_cases == [{"query": "hi"}]


@pytest.mark.asyncio
async def test_dataset_store_get_missing_returns_none() -> None:
    from ai.src.infrastructure.chat_evaluation.dataset_store import InMemoryDatasetStore

    store = InMemoryDatasetStore()
    assert await store.get("nope") is None


def test_get_dataset_store_returns_singleton() -> None:
    from ai.src.infrastructure.chat_evaluation.dataset_store import get_dataset_store

    assert get_dataset_store() is get_dataset_store()


# ── E2EScorer ─────────────────────────────────────────────────────────────────


def test_score_e2e_sync_collects_results() -> None:
    from ai.src.infrastructure.chat_evaluation import scorer as mod

    metric = MagicMock()
    metric.score = 0.9
    metric.is_successful.return_value = True
    metric.reason = "highly relevant"

    with patch.object(mod, "_build_e2e_metrics", return_value=[("answer_relevancy", metric)]):
        results = mod._score_e2e_sync("gpt-4o", 0.7, "q", "actual", "expected", ["ctx"])

    assert len(results) == 1
    assert results[0].name == "answer_relevancy"
    assert results[0].score == 0.9
    assert results[0].success is True
    assert results[0].reason == "highly relevant"
    metric.measure.assert_called_once()


def test_score_e2e_sync_isolates_metric_failure() -> None:
    from ai.src.infrastructure.chat_evaluation import scorer as mod

    bad = MagicMock()
    bad.measure.side_effect = RuntimeError("timeout")

    with patch.object(mod, "_build_e2e_metrics", return_value=[("faithfulness", bad)]):
        results = mod._score_e2e_sync("gpt-4o", 0.7, "q", "a", "e", ["c"])

    assert results[0].success is False
    assert results[0].score == 0.0
    assert "timeout" in results[0].reason


@pytest.mark.asyncio
async def test_e2e_scorer_delegates_to_thread(monkeypatch) -> None:
    from ai.src.infrastructure.chat_evaluation import scorer as mod

    monkeypatch.setattr(mod, "_score_e2e_sync", lambda *a: ["m1"])
    result = await mod.E2EScorer(model="gpt-4o").score("q", "a", "e", ["ctx"])
    assert result == ["m1"]


def test_build_e2e_metrics_returns_named_metrics() -> None:
    from ai.src.infrastructure.chat_evaluation import scorer as mod

    answer_mock = MagicMock()
    faith_mock = MagicMock()

    with (
        patch("deepeval.metrics.AnswerRelevancyMetric", return_value=answer_mock),
        patch("deepeval.metrics.FaithfulnessMetric", return_value=faith_mock),
    ):
        metrics = mod._build_e2e_metrics("gpt-4o", 0.7)

    names = [name for name, _ in metrics]
    assert "answer_relevancy" in names
    assert "faithfulness" in names
    assert len(metrics) == 2


# ── KBRelevancyScorer ─────────────────────────────────────────────────────────


def test_score_kb_relevancy_sync_returns_metric() -> None:
    from ai.src.infrastructure.chat_evaluation import scorer as mod

    metric = MagicMock()
    metric.score = 0.75
    metric.is_successful.return_value = True
    metric.reason = "relevant chunks"

    with patch("deepeval.metrics.ContextualRelevancyMetric", return_value=metric):
        result = mod._score_kb_relevancy_sync("gpt-4o", 0.7, "q", ["chunk1"])

    assert result.name == "kb_relevancy"
    assert result.score == 0.75
    assert result.success is True


def test_score_kb_relevancy_sync_isolates_failure() -> None:
    from ai.src.infrastructure.chat_evaluation import scorer as mod

    bad_metric = MagicMock()
    bad_metric.measure.side_effect = RuntimeError("deepeval error")

    with patch("deepeval.metrics.ContextualRelevancyMetric", return_value=bad_metric):
        result = mod._score_kb_relevancy_sync("gpt-4o", 0.7, "q", ["chunk"])

    assert result.success is False
    assert result.score == 0.0
    assert "deepeval error" in result.reason


@pytest.mark.asyncio
async def test_kb_relevancy_scorer_delegates_to_thread(monkeypatch) -> None:
    from ai.src.infrastructure.chat_evaluation import scorer as mod
    from ai.src.domain.chat_evaluation.entities import MetricResult

    fake_result = MetricResult(name="kb_relevancy", score=0.8, threshold=0.7, success=True)
    monkeypatch.setattr(mod, "_score_kb_relevancy_sync", lambda *a: fake_result)

    result = await mod.KBRelevancyScorer(model="gpt-4o").score("q", ["ctx"])
    assert result.score == 0.8


# ── ConversationScorer ────────────────────────────────────────────────────────


def test_score_metric_sync_success() -> None:
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    from ai.src.infrastructure.chat_evaluation import conversation_scorer as mod

    metric = MagicMock()
    metric.score = 0.82
    metric.is_successful.return_value = True
    metric.reason = "Conversation is coherent and helpful."

    test_case = LLMTestCase(
        input="scenario",
        actual_output="Turn 1\n  Customer: q\n  Agent: a",
    )

    with patch(
        "ai.src.infrastructure.chat_evaluation.conversation_scorer.GEval",
        return_value=metric,
    ):
        result = mod._score_metric_sync(
            "conversation_quality",
            "Does the agent respond helpfully?",
            [LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            "gpt-4o",
            0.5,
            test_case,
        )

    assert result.name == "conversation_quality"
    assert result.score == 0.82
    assert result.success is True
    metric.measure.assert_called_once_with(test_case)


def test_score_metric_sync_isolates_failure() -> None:
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    from ai.src.infrastructure.chat_evaluation import conversation_scorer as mod

    bad_metric = MagicMock()
    bad_metric.measure.side_effect = RuntimeError("GEval timeout")

    test_case = LLMTestCase(
        input="scenario",
        actual_output="Turn 1\n  Customer: fees?\n  Agent: 0%",
    )

    with patch(
        "ai.src.infrastructure.chat_evaluation.conversation_scorer.GEval",
        return_value=bad_metric,
    ):
        result = mod._score_metric_sync(
            "kb_utilization",
            "Does the agent use the KB?",
            [LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
            "gpt-4o",
            0.5,
            test_case,
        )

    assert result.success is False
    assert result.score == 0.0
    assert "GEval timeout" in result.reason


def test_format_conversation_renders_turns() -> None:
    from ai.src.infrastructure.chat_evaluation import conversation_scorer as mod

    turns = [
        {"user": "Where is my transfer?", "agent_actual": "I'll check."},
        {"user": "Thanks!", "agent_expected": "You're welcome."},
    ]
    text = mod._format_conversation(turns)
    assert "Turn 1" in text
    assert "Where is my transfer?" in text
    assert "I'll check." in text
    assert "Turn 2" in text
    assert "Thanks!" in text


@pytest.mark.asyncio
async def test_conversation_scorer_parallel_metrics(monkeypatch) -> None:
    from ai.src.infrastructure.chat_evaluation import conversation_scorer as mod
    from ai.src.domain.chat_evaluation.entities import MetricResult

    fake = MetricResult(name="stub", score=0.9, threshold=0.5, success=True)
    monkeypatch.setattr(mod, "_score_metric_sync", lambda *a: fake)

    result = await mod.ConversationScorer(model="gpt-4o").score(
        scenario_description="Fees",
        conversation_turns=[{"user": "fees?", "agent_actual": "0%"}],
        rules=["Never reveal PINs"],
        kb_descriptions=["Afriex FAQ"],
    )
    assert len(result) == 3
    assert all(r.score == 0.9 for r in result)


@pytest.mark.asyncio
async def test_conversation_scorer_gather_error_returns_fallback(
    monkeypatch,
) -> None:
    from ai.src.infrastructure.chat_evaluation import conversation_scorer as mod
    from ai.src.domain.chat_evaluation.entities import MetricResult

    call_count = 0

    def _first_fails(*a):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("thread error")
        return MetricResult(name="stub", score=0.8, threshold=0.5, success=True)

    monkeypatch.setattr(mod, "_score_metric_sync", _first_fails)

    result = await mod.ConversationScorer(model="gpt-4o").score(
        scenario_description="Fees",
        conversation_turns=[{"user": "q", "agent_actual": "a"}],
        rules=[],
        kb_descriptions=[],
    )
    assert len(result) == 3
    assert result[0].success is False
    assert "thread error" in result[0].reason


# ── ScenarioLabelJudge ────────────────────────────────────────────────────────


def test_build_user_prompt_contains_query_and_scenario() -> None:
    from ai.src.infrastructure.chat_evaluation.scenario_labeler import (
        _build_user_prompt,
    )

    prompt = _build_user_prompt(
        "my transfer is stuck",
        [("scn-1", "Transfer Issues", "Handles delayed transfers")],
    )
    assert "my transfer is stuck" in prompt
    assert "scn-1" in prompt
    assert "Transfer Issues" in prompt


def test_build_user_prompt_multiple_scenarios() -> None:
    from ai.src.infrastructure.chat_evaluation.scenario_labeler import (
        _build_user_prompt,
    )

    prompt = _build_user_prompt(
        "fee question",
        [
            ("s1", "Fees", "Fee queries"),
            ("s2", "Transfers", "Transfer help"),
        ],
    )
    assert "s1" in prompt
    assert "s2" in prompt
    assert "scenario_ids" in prompt


@pytest.mark.asyncio
async def test_judge_returns_empty_when_no_scenarios() -> None:
    from ai.src.infrastructure.chat_evaluation.scenario_labeler import ScenarioLabelJudge

    judge = ScenarioLabelJudge()
    ids, reason = await judge.label("query", [])
    assert ids == []
    assert "No scenarios" in reason


@pytest.mark.asyncio
async def test_judge_returns_ids_on_success() -> None:
    from ai.src.infrastructure.chat_evaluation.scenario_labeler import ScenarioLabelJudge
    from ai.src.domain.llm.types import StructuredSingleTaskAgentResult

    result = MagicMock(spec=StructuredSingleTaskAgentResult)
    result.parse_success = True
    result.data = {"scenario_ids": ["scn-1", "scn-2"], "reason": "Both match"}
    result.raw = None

    runner_mock = MagicMock()
    runner_mock.run_structured = MagicMock(return_value=result)

    with patch(
        "ai.src.infrastructure.chat_evaluation.scenario_labeler"
        ".SingleTaskAgentRunner",
        return_value=runner_mock,
    ):
        judge = ScenarioLabelJudge()
        # replace runner directly to avoid __init__ constructing a real one
        judge._runner = runner_mock
        runner_mock.run_structured = AsyncMock(return_value=result)
        ids, reason = await judge.label("transfer delay", [("scn-1", "Transfer", "desc")])

    assert ids == ["scn-1", "scn-2"]
    assert reason == "Both match"


@pytest.mark.asyncio
async def test_judge_returns_empty_on_runner_exception() -> None:
    from ai.src.infrastructure.chat_evaluation.scenario_labeler import ScenarioLabelJudge

    judge = ScenarioLabelJudge()
    runner_mock = MagicMock()
    runner_mock.run_structured = AsyncMock(side_effect=RuntimeError("LLM error"))
    judge._runner = runner_mock

    ids, reason = await judge.label("query", [("scn-1", "Fees", "desc")])
    assert ids == []
    assert "failed" in reason


@pytest.mark.asyncio
async def test_judge_returns_empty_when_parse_fails() -> None:
    from ai.src.infrastructure.chat_evaluation.scenario_labeler import ScenarioLabelJudge

    result = MagicMock()
    result.parse_success = False
    result.data = None
    result.raw = "invalid json"

    judge = ScenarioLabelJudge()
    runner_mock = MagicMock()
    runner_mock.run_structured = AsyncMock(return_value=result)
    judge._runner = runner_mock

    ids, reason = await judge.label("query", [("scn-1", "Fees", "desc")])
    assert ids == []
    assert reason == "invalid json"


@pytest.mark.asyncio
async def test_judge_filters_falsy_scenario_ids() -> None:
    from ai.src.infrastructure.chat_evaluation.scenario_labeler import ScenarioLabelJudge

    result = MagicMock()
    result.parse_success = True
    result.data = {"scenario_ids": ["scn-1", "", None, "scn-2"], "reason": "ok"}

    judge = ScenarioLabelJudge()
    runner_mock = MagicMock()
    runner_mock.run_structured = AsyncMock(return_value=result)
    judge._runner = runner_mock

    ids, _ = await judge.label("query", [("scn-1", "A", "desc")])
    assert ids == ["scn-1", "scn-2"]


# ── build_chat_evaluation_pipeline ────────────────────────────────────────────

_BUILD_RETRIEVAL_PATH = (
    "ai.src.application.retrieval.dependencies.build_retrieval_pipeline"
)


def _patch_pipeline_deps():
    """Context managers that prevent real OpenAI/Pinecone clients from being created."""
    from unittest.mock import patch, MagicMock
    return [
        patch(
            "ai.src.infrastructure.llm.embedder.OpenAI",
            return_value=MagicMock(),
        ),
        patch(
            "ai.src.infrastructure.vector_store.pinecone.PineconeVectorStore.__init__",
            return_value=None,
        ),
        patch(
            "ai.src.infrastructure.chat_evaluation.run_store.get_run_store",
            return_value=MagicMock(),
        ),
    ]


def test_build_pipeline_input_guardrail_mode() -> None:
    from contextlib import ExitStack
    from ai.src.application.chat_evaluation.dependencies import (
        build_chat_evaluation_pipeline,
    )
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    with ExitStack() as stack:
        for p in _patch_pipeline_deps():
            stack.enter_context(p)
        pipeline = build_chat_evaluation_pipeline("input_guardrail")

    assert isinstance(pipeline, ChatEvaluationPipeline)


def test_build_pipeline_output_guardrail_mode() -> None:
    from contextlib import ExitStack
    from ai.src.application.chat_evaluation.dependencies import (
        build_chat_evaluation_pipeline,
    )
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    with ExitStack() as stack:
        for p in _patch_pipeline_deps():
            stack.enter_context(p)
        pipeline = build_chat_evaluation_pipeline("output_guardrail")

    assert isinstance(pipeline, ChatEvaluationPipeline)


def test_build_pipeline_scenario_mode() -> None:
    from contextlib import ExitStack
    from ai.src.application.chat_evaluation.dependencies import (
        build_chat_evaluation_pipeline,
    )
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    with ExitStack() as stack:
        for p in _patch_pipeline_deps():
            stack.enter_context(p)
        pipeline = build_chat_evaluation_pipeline("scenario")

    assert isinstance(pipeline, ChatEvaluationPipeline)


def test_build_pipeline_e2e_mode() -> None:
    from contextlib import ExitStack
    from ai.src.application.chat_evaluation.dependencies import (
        build_chat_evaluation_pipeline,
    )
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    with ExitStack() as stack:
        for p in _patch_pipeline_deps():
            stack.enter_context(p)
        pipeline = build_chat_evaluation_pipeline("e2e")

    assert isinstance(pipeline, ChatEvaluationPipeline)


def test_build_pipeline_conversation_synthetic_mode() -> None:
    from contextlib import ExitStack
    from ai.src.application.chat_evaluation.dependencies import (
        build_chat_evaluation_pipeline,
    )
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    with ExitStack() as stack:
        for p in _patch_pipeline_deps():
            stack.enter_context(p)
        pipeline = build_chat_evaluation_pipeline("conversation", "synthetic")

    assert isinstance(pipeline, ChatEvaluationPipeline)


def test_build_pipeline_conversation_real_mode() -> None:
    from contextlib import ExitStack
    from ai.src.application.chat_evaluation.dependencies import (
        build_chat_evaluation_pipeline,
    )
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    with ExitStack() as stack:
        for p in _patch_pipeline_deps():
            stack.enter_context(p)
        pipeline = build_chat_evaluation_pipeline("conversation", "real")

    assert isinstance(pipeline, ChatEvaluationPipeline)


def test_build_pipeline_unknown_mode_raises() -> None:
    from contextlib import ExitStack
    from ai.src.application.chat_evaluation.dependencies import (
        build_chat_evaluation_pipeline,
    )

    with ExitStack() as stack:
        for p in _patch_pipeline_deps():
            stack.enter_context(p)
        with pytest.raises(ValueError, match="Unknown eval_mode"):
            build_chat_evaluation_pipeline("nonexistent_mode")
