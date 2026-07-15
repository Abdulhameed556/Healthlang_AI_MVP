"""Unit tests: ai/src/application/chat_evaluation/pipeline.py + context.py"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.domain.chat_evaluation.entities import (
    EvalMode,
    GuardrailCaseResult,
    ScenarioCaseResult,
    OutputGuardrailCaseResult,
    E2ETurnResult,
    MetricResult,
    RunStatus,
)


# ── helpers ───────────────────────────────────────────────────────────────────


def _make_ctx(eval_mode=EvalMode.INPUT_GUARDRAIL, results=None, **kwargs):
    from ai.src.application.chat_evaluation.context import ChatEvalContext

    return ChatEvalContext(
        run_id="run-1",
        eval_mode=eval_mode,
        test_cases=[],
        results=results or [],
        **kwargs,
    )


def _guardrail_result(expected_blocked: bool, actual_status: str) -> GuardrailCaseResult:
    correct = (actual_status == "block") == expected_blocked
    return GuardrailCaseResult(
        query="q",
        expected_blocked=expected_blocked,
        actual_status=actual_status,
        correct=correct,
    )


def _scenario_result(scenario_correct=True, kb_score=None, kb_selected=None):
    return ScenarioCaseResult(
        query="q",
        scenario_correct=scenario_correct,
        actual_scenario_ids=[],
        expected_scenario_ids=[],
        kb_relevancy_score=kb_score,
        kb_id_selected=kb_selected,
        reason="",
    )


def _output_result(correct=True):
    return OutputGuardrailCaseResult(
        query="q", expected_action="pass", actual_status="pass", correct=correct
    )


def _e2e_result(*metric_pairs):
    metrics = [
        MetricResult(name=n, score=s, threshold=0.7, success=s >= 0.7)
        for n, s in metric_pairs
    ]
    return E2ETurnResult(
        query="q",
        expected_answer="e",
        actual_response="a",
        input_guardrail_status="pass",
        scenario_ids=[],
        kb_id_selected=None,
        chunks_retrieved=0,
        output_guardrail_status="pass",
        metrics=metrics,
    )


# ── _aggregate: input_guardrail ───────────────────────────────────────────────


def test_aggregate_guardrail_accuracy() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate

    results = [
        _guardrail_result(False, "pass"),   # TN — correct
        _guardrail_result(True, "block"),   # TP — correct
        _guardrail_result(False, "block"),  # FP — wrong
        _guardrail_result(True, "pass"),    # FN — wrong
    ]
    scores = _aggregate(EvalMode.INPUT_GUARDRAIL, results)

    assert scores["accuracy"] == pytest.approx(0.5)
    assert scores["false_positive_rate"] == pytest.approx(0.5)   # 1 FP / 2 safe
    assert scores["false_negative_rate"] == pytest.approx(0.5)   # 1 FN / 2 attacks


def test_aggregate_guardrail_empty_returns_empty() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate

    assert _aggregate(EvalMode.INPUT_GUARDRAIL, []) == {}


def test_aggregate_guardrail_all_correct() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate

    results = [_guardrail_result(False, "pass"), _guardrail_result(True, "block")]
    scores = _aggregate(EvalMode.INPUT_GUARDRAIL, results)
    assert scores["accuracy"] == pytest.approx(1.0)
    assert scores["false_positive_rate"] == pytest.approx(0.0)
    assert scores["false_negative_rate"] == pytest.approx(0.0)


# ── _aggregate: scenario ──────────────────────────────────────────────────────


def test_aggregate_scenario_with_kb_scores() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate

    results = [
        _scenario_result(True, kb_score=0.8, kb_selected="kb-1"),
        _scenario_result(False, kb_score=0.6, kb_selected="kb-2"),
        _scenario_result(True, kb_score=None, kb_selected=None),
    ]
    scores = _aggregate(EvalMode.SCENARIO, results)

    assert scores["scenario_accuracy"] == pytest.approx(2 / 3)
    assert scores["kb_relevancy_mean"] == pytest.approx(0.7)
    assert scores["kb_selection_rate"] == pytest.approx(2 / 3)


def test_aggregate_scenario_no_kb_scores() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate

    results = [_scenario_result(True)]
    scores = _aggregate(EvalMode.SCENARIO, results)
    assert "kb_relevancy_mean" not in scores


# ── _aggregate: output_guardrail ─────────────────────────────────────────────


def test_aggregate_output_guardrail_accuracy() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate

    results = [_output_result(True), _output_result(True), _output_result(False)]
    scores = _aggregate(EvalMode.OUTPUT_GUARDRAIL, results)
    assert scores["action_accuracy"] == pytest.approx(2 / 3)


# ── _aggregate: e2e ───────────────────────────────────────────────────────────


def test_aggregate_e2e_means_metrics() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate

    results = [
        _e2e_result(("answer_relevancy", 0.8), ("faithfulness", 0.9)),
        _e2e_result(("answer_relevancy", 0.6), ("faithfulness", 0.7)),
    ]
    scores = _aggregate(EvalMode.E2E, results)
    assert scores["answer_relevancy"] == pytest.approx(0.7)
    assert scores["faithfulness"] == pytest.approx(0.8)


def test_aggregate_unknown_mode_returns_empty() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate

    assert _aggregate("unknown_mode", [_output_result()]) == {}


# ── _aggregate: conversation ──────────────────────────────────────────────────


def _conv_result(scenario_id: str, scores: dict, judge_scores: dict | None = None):
    from ai.src.domain.chat_evaluation.entities import ConversationCaseResult

    return ConversationCaseResult(
        scenario_id=scenario_id,
        scenario_name="Test Scenario",
        persona="frustrated_customer",
        run_index=0,
        scores=scores,
        judge_scores=judge_scores or {},
    )


def test_aggregate_conversation_means_metric_scores() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate
    from ai.src.domain.chat_evaluation.entities import EvalMode

    results = [
        _conv_result("scn-1", {"conversation_quality": 0.8, "kb_utilization": 0.6}),
        _conv_result("scn-1", {"conversation_quality": 0.6, "kb_utilization": 0.8}),
    ]
    scores = _aggregate(EvalMode.CONVERSATION, results)

    assert scores["conversation_quality"] == pytest.approx(0.7)
    assert scores["kb_utilization"] == pytest.approx(0.7)


def test_aggregate_conversation_counts_distinct_scenarios() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate
    from ai.src.domain.chat_evaluation.entities import EvalMode

    results = [
        _conv_result("scn-1", {"conversation_quality": 0.8}),
        _conv_result("scn-1", {"conversation_quality": 0.7}),  # same scenario
        _conv_result("scn-2", {"conversation_quality": 0.9}),
    ]
    scores = _aggregate(EvalMode.CONVERSATION, results)

    assert scores["scenarios_covered"] == 2.0


def test_aggregate_conversation_empty_returns_empty() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate
    from ai.src.domain.chat_evaluation.entities import EvalMode

    assert _aggregate(EvalMode.CONVERSATION, []) == {}


# ── ChatEvaluationPipeline ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pipeline_completes_and_saves_results() -> None:
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    async def _inject_results(ctx):
        ctx.results = [_guardrail_result(False, "pass"), _guardrail_result(True, "block")]

    step = MagicMock()
    step.run = AsyncMock(side_effect=_inject_results)
    store = AsyncMock()

    ctx = _make_ctx(eval_mode=EvalMode.INPUT_GUARDRAIL)
    pipeline = ChatEvaluationPipeline([step], store)
    report = await pipeline.run(ctx)

    assert report.status == RunStatus.COMPLETED
    assert report.aggregate_scores["accuracy"] == pytest.approx(1.0)
    assert store.save.await_count == 2   # RUNNING then COMPLETED


@pytest.mark.asyncio
async def test_pipeline_marks_failed_on_step_error() -> None:
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    step = MagicMock()
    step.run = AsyncMock(side_effect=RuntimeError("boom"))
    store = AsyncMock()

    report = await ChatEvaluationPipeline([step], store).run(_make_ctx())

    assert report.status == RunStatus.FAILED
    assert "boom" in report.error
    assert store.save.await_count == 2


@pytest.mark.asyncio
async def test_pipeline_propagates_agent_id() -> None:
    from ai.src.application.chat_evaluation.pipeline import ChatEvaluationPipeline

    step = MagicMock()
    step.run = AsyncMock()
    store = AsyncMock()

    ctx = _make_ctx(agent_id="agent-uuid-123")
    report = await ChatEvaluationPipeline([step], store).run(ctx)

    assert report.agent_id == "agent-uuid-123"


# ── ChatEvalContext ────────────────────────────────────────────────────────────


def test_context_defaults() -> None:
    from ai.src.application.chat_evaluation.context import ChatEvalContext

    ctx = ChatEvalContext(run_id="r", eval_mode="e2e", test_cases=[])
    assert ctx.agent_id is None
    assert ctx.model_overrides == {}
    assert ctx.results == []
    assert ctx.conversations == []
    assert ctx.determinism_runs == 1


def test_context_determinism_runs_settable() -> None:
    from ai.src.application.chat_evaluation.context import ChatEvalContext

    ctx = ChatEvalContext(
        run_id="r", eval_mode="conversation", test_cases=[], determinism_runs=3
    )
    assert ctx.determinism_runs == 3


# ── ChatEvalContext: new conversation-mode fields ─────────────────────────────


def test_context_conversation_fields_default() -> None:
    from ai.src.application.chat_evaluation.context import ChatEvalContext

    ctx = ChatEvalContext(run_id="r", eval_mode="conversation", test_cases=[])

    assert ctx.first_speaker == "human_sim"
    assert ctx.welcome_message == ""
    assert ctx.agent_variables == {}
    assert ctx.api_tool_mocks == {}
    assert ctx.judge_criteria == []
    assert ctx.max_minutes == 10


def test_context_conversation_fields_settable() -> None:
    from ai.src.application.chat_evaluation.context import ChatEvalContext

    ctx = ChatEvalContext(
        run_id="r",
        eval_mode="conversation",
        test_cases=[],
        first_speaker="agent",
        welcome_message="Hello, how can I help?",
        agent_variables={"customer_id": "cus_123", "support_tier": "Gold"},
        api_tool_mocks={"stripe_payments": {"status": "success", "balance": 450}},
        judge_criteria=["Agent stayed on topic."],
        max_minutes=5,
    )

    assert ctx.first_speaker == "agent"
    assert ctx.welcome_message == "Hello, how can I help?"
    assert ctx.agent_variables["support_tier"] == "Gold"
    assert ctx.api_tool_mocks["stripe_payments"]["balance"] == 450
    assert ctx.judge_criteria == ["Agent stayed on topic."]
    assert ctx.max_minutes == 5


def test_context_agent_variables_independent_across_instances() -> None:
    from ai.src.application.chat_evaluation.context import ChatEvalContext

    ctx_a = ChatEvalContext(run_id="a", eval_mode="e", test_cases=[])
    ctx_b = ChatEvalContext(run_id="b", eval_mode="e", test_cases=[])
    ctx_a.agent_variables["x"] = "1"

    assert "x" not in ctx_b.agent_variables


# ── ConversationCaseResult: judge_scores field ────────────────────────────────


def test_conversation_case_result_judge_scores_default() -> None:
    from ai.src.domain.chat_evaluation.entities import ConversationCaseResult

    result = ConversationCaseResult(
        scenario_id="s1",
        scenario_name="Test",
        persona="calm_detailed",
        run_index=0,
    )

    assert result.judge_scores == {}


def test_conversation_case_result_judge_scores_settable() -> None:
    from ai.src.domain.chat_evaluation.entities import ConversationCaseResult

    result = ConversationCaseResult(
        scenario_id="s1",
        scenario_name="Test",
        persona="calm_detailed",
        run_index=0,
        judge_scores={
            "tone": {"score": 0.9, "reason": "polite tone throughout"},
            "accuracy": {"score": 0.7, "reason": "mostly accurate"},
        },
    )

    assert result.judge_scores["tone"]["score"] == pytest.approx(0.9)
    assert result.judge_scores["tone"]["reason"] == "polite tone throughout"
    assert result.judge_scores["accuracy"]["score"] == pytest.approx(0.7)


def test_aggregate_conversation_includes_judge_score() -> None:
    from ai.src.application.chat_evaluation.pipeline import _aggregate
    from ai.src.domain.chat_evaluation.entities import EvalMode

    results = [
        _conv_result(
            "scn-1",
            {"conversation_quality": 0.8},
            judge_scores={
                "Tone": {"score": 1.0, "reason": "polite"},
                "Accuracy": {"score": 0.5, "reason": "partial"},
            },
        ),
        _conv_result(
            "scn-2",
            {"conversation_quality": 0.7},
            judge_scores={
                "Tone": {"score": 0.5, "reason": "neutral"},
                "Accuracy": {"score": 0.0, "reason": "missed"},
            },
        ),
    ]
    scores = _aggregate(EvalMode.CONVERSATION, results)

    # mean of [1.0, 0.5, 0.5, 0.0] = 0.5
    assert scores["judge_score"] == pytest.approx(0.5)
