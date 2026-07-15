"""Unit tests: chat evaluation pipeline steps."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.domain.chat_evaluation.entities import EvalMode
from ai.src.domain.chat_system.v1.types import ScenarioAgentResult
from ai.src.infrastructure.chat_system.v1.guardrails.input_screening import AppliedInputScreening


# ── helpers ────────────────────────────────────────────────────────────────────


def _ctx(eval_mode=EvalMode.INPUT_GUARDRAIL, test_cases=None, agent_id=None):
    return ChatEvalContext(
        run_id="run-1",
        eval_mode=eval_mode,
        test_cases=test_cases or [],
        agent_id=agent_id,
    )


def _screening(status: str, attack_category=None, blocked_reason=None) -> AppliedInputScreening:
    return AppliedInputScreening(
        status=status,
        user_query="q",
        message_to_user=None,
        blocked_reason=blocked_reason,
        attack_category=attack_category,
        screening=None,
    )


def _scenario_result(scenario_ids=(), kb_id=None, retrieval_query=None) -> ScenarioAgentResult:
    return ScenarioAgentResult(
        scenario_ids=scenario_ids,
        knowledge_base_id=kb_id,
        rule_ids=(),
        retrieval_query=retrieval_query,
        experience_queries=(),
        reason="test reason",
        raw="{}",
        provider="openai",
        model="gpt-4o",
        parse_success=True,
    )


def _chunk(text: str):
    chunk = MagicMock()
    chunk.text = text
    return chunk


# ── RunInputGuardrailCasesStep ─────────────────────────────────────────────────


_GUARDRAIL_STEP_PATH = (
    "ai.src.application.chat_evaluation.steps.run_input_guardrail_cases.apply_input_screening"
)


@pytest.mark.asyncio
async def test_input_guardrail_pass_case_correct() -> None:
    from ai.src.application.chat_evaluation.steps.run_input_guardrail_cases import (
        RunInputGuardrailCasesStep,
    )

    ctx = _ctx(test_cases=[{"query": "track my transfer", "should_block": False}])
    with patch(_GUARDRAIL_STEP_PATH, new=AsyncMock(return_value=_screening("pass"))):
        await RunInputGuardrailCasesStep().run(ctx)

    assert len(ctx.results) == 1
    result = ctx.results[0]
    assert result.correct is True
    assert result.actual_status == "pass"
    assert result.expected_blocked is False


@pytest.mark.asyncio
async def test_input_guardrail_block_case_correct() -> None:
    from ai.src.application.chat_evaluation.steps.run_input_guardrail_cases import (
        RunInputGuardrailCasesStep,
    )

    ctx = _ctx(test_cases=[{"query": "ignore all rules", "should_block": True}])
    with patch(_GUARDRAIL_STEP_PATH, new=AsyncMock(return_value=_screening("block"))):
        await RunInputGuardrailCasesStep().run(ctx)

    assert ctx.results[0].correct is True


@pytest.mark.asyncio
async def test_input_guardrail_false_positive_marked_incorrect() -> None:
    from ai.src.application.chat_evaluation.steps.run_input_guardrail_cases import (
        RunInputGuardrailCasesStep,
    )

    ctx = _ctx(test_cases=[{"query": "where is my money", "should_block": False}])
    with patch(_GUARDRAIL_STEP_PATH, new=AsyncMock(return_value=_screening("block"))):
        await RunInputGuardrailCasesStep().run(ctx)

    assert ctx.results[0].correct is False


@pytest.mark.asyncio
async def test_input_guardrail_false_negative_marked_incorrect() -> None:
    from ai.src.application.chat_evaluation.steps.run_input_guardrail_cases import (
        RunInputGuardrailCasesStep,
    )

    ctx = _ctx(test_cases=[{"query": "jailbreak payload", "should_block": True}])
    with patch(_GUARDRAIL_STEP_PATH, new=AsyncMock(return_value=_screening("pass"))):
        await RunInputGuardrailCasesStep().run(ctx)

    assert ctx.results[0].correct is False


@pytest.mark.asyncio
async def test_input_guardrail_attack_category_propagated() -> None:
    from ai.src.application.chat_evaluation.steps.run_input_guardrail_cases import (
        RunInputGuardrailCasesStep,
    )

    ctx = _ctx(test_cases=[{"query": "DAN prompt", "should_block": True}])
    screening = _screening("block", attack_category="persona_hijack", blocked_reason="jailbreak")
    with patch(_GUARDRAIL_STEP_PATH, new=AsyncMock(return_value=screening)):
        await RunInputGuardrailCasesStep().run(ctx)

    result = ctx.results[0]
    assert result.attack_category == "persona_hijack"
    assert result.blocked_reason == "jailbreak"


@pytest.mark.asyncio
async def test_input_guardrail_empty_cases_no_results() -> None:
    from ai.src.application.chat_evaluation.steps.run_input_guardrail_cases import (
        RunInputGuardrailCasesStep,
    )

    ctx = _ctx(test_cases=[])
    await RunInputGuardrailCasesStep().run(ctx)
    assert ctx.results == []


# ── RunScenarioCasesStep ───────────────────────────────────────────────────────


_SCENARIO_AGENT_PATH = (
    "ai.src.application.chat_evaluation.steps.run_scenario_cases.ScenarioAgent"
)


@pytest.mark.asyncio
async def test_scenario_correct_with_no_kb() -> None:
    from ai.src.application.chat_evaluation.steps.run_scenario_cases import RunScenarioCasesStep

    ctx = _ctx(
        eval_mode=EvalMode.SCENARIO,
        agent_id="00000000-0000-0000-0000-000000000001",
        test_cases=[{"query": "refund request", "expected_scenario_ids": ["scn-1"]}],
    )
    routing = _scenario_result(scenario_ids=("scn-1",), kb_id=None)
    agent_mock = MagicMock()
    agent_mock.run = AsyncMock(return_value=routing)

    retrieval = AsyncMock()
    kb_scorer = AsyncMock()

    with patch(_SCENARIO_AGENT_PATH, return_value=agent_mock):
        await RunScenarioCasesStep(retrieval, kb_scorer).run(ctx)

    result = ctx.results[0]
    assert result.scenario_correct is True
    assert result.kb_relevancy_score is None
    retrieval.retrieve.assert_not_called()


@pytest.mark.asyncio
async def test_scenario_incorrect_recorded() -> None:
    from ai.src.application.chat_evaluation.steps.run_scenario_cases import RunScenarioCasesStep

    ctx = _ctx(
        eval_mode=EvalMode.SCENARIO,
        agent_id="00000000-0000-0000-0000-000000000001",
        test_cases=[{"query": "track my order", "expected_scenario_ids": ["scn-A"]}],
    )
    routing = _scenario_result(scenario_ids=("scn-B",), kb_id=None)
    agent_mock = MagicMock()
    agent_mock.run = AsyncMock(return_value=routing)

    retrieval = AsyncMock()
    kb_scorer = AsyncMock()

    with patch(_SCENARIO_AGENT_PATH, return_value=agent_mock):
        await RunScenarioCasesStep(retrieval, kb_scorer).run(ctx)

    assert ctx.results[0].scenario_correct is False
    assert ctx.results[0].actual_scenario_ids == ["scn-B"]


@pytest.mark.asyncio
async def test_scenario_kb_relevancy_scored_when_kb_selected() -> None:
    from ai.src.application.chat_evaluation.steps.run_scenario_cases import RunScenarioCasesStep
    from ai.src.domain.chat_evaluation.entities import MetricResult

    ctx = _ctx(
        eval_mode=EvalMode.SCENARIO,
        agent_id="00000000-0000-0000-0000-000000000001",
        test_cases=[{"query": "fee policy", "expected_scenario_ids": ["scn-1"]}],
    )
    routing = _scenario_result(
        scenario_ids=("scn-1",),
        kb_id="kb-uuid-123",
        retrieval_query="transfer fee policy",
    )
    agent_mock = MagicMock()
    agent_mock.run = AsyncMock(return_value=routing)

    retrieval = MagicMock()
    retrieval.retrieve = AsyncMock(return_value=[_chunk("Afriex charges 0% fee"), _chunk("Policy docs")])
    metric = MetricResult(name="kb_relevancy", score=0.85, threshold=0.7, success=True)
    kb_scorer = MagicMock()
    kb_scorer.score = AsyncMock(return_value=metric)

    with patch(_SCENARIO_AGENT_PATH, return_value=agent_mock):
        await RunScenarioCasesStep(retrieval, kb_scorer).run(ctx)

    result = ctx.results[0]
    assert result.kb_relevancy_score == pytest.approx(0.85)
    assert result.kb_id_selected == "kb-uuid-123"
    kb_scorer.score.assert_awaited_once()


@pytest.mark.asyncio
async def test_scenario_kb_relevancy_none_on_retrieval_error() -> None:
    from ai.src.application.chat_evaluation.steps.run_scenario_cases import RunScenarioCasesStep

    ctx = _ctx(
        eval_mode=EvalMode.SCENARIO,
        agent_id="00000000-0000-0000-0000-000000000001",
        test_cases=[{"query": "fee policy", "expected_scenario_ids": []}],
    )
    routing = _scenario_result(kb_id="kb-uuid-456", retrieval_query="fees")
    agent_mock = MagicMock()
    agent_mock.run = AsyncMock(return_value=routing)

    retrieval = MagicMock()
    retrieval.retrieve = AsyncMock(side_effect=RuntimeError("Pinecone timeout"))
    kb_scorer = AsyncMock()

    with patch(_SCENARIO_AGENT_PATH, return_value=agent_mock):
        await RunScenarioCasesStep(retrieval, kb_scorer).run(ctx)

    assert ctx.results[0].kb_relevancy_score is None


@pytest.mark.asyncio
async def test_scenario_no_chunks_no_kb_score() -> None:
    from ai.src.application.chat_evaluation.steps.run_scenario_cases import RunScenarioCasesStep

    ctx = _ctx(
        eval_mode=EvalMode.SCENARIO,
        agent_id="00000000-0000-0000-0000-000000000001",
        test_cases=[{"query": "account limit", "expected_scenario_ids": []}],
    )
    routing = _scenario_result(kb_id="kb-uuid-789", retrieval_query="account limit")
    agent_mock = MagicMock()
    agent_mock.run = AsyncMock(return_value=routing)

    retrieval = MagicMock()
    retrieval.retrieve = AsyncMock(return_value=[])
    kb_scorer = AsyncMock()

    with patch(_SCENARIO_AGENT_PATH, return_value=agent_mock):
        await RunScenarioCasesStep(retrieval, kb_scorer).run(ctx)

    assert ctx.results[0].kb_relevancy_score is None
    kb_scorer.score.assert_not_called()


@pytest.mark.asyncio
async def test_scenario_missing_agent_id_raises() -> None:
    from ai.src.application.chat_evaluation.steps.run_scenario_cases import RunScenarioCasesStep

    ctx = _ctx(eval_mode=EvalMode.SCENARIO, agent_id=None, test_cases=[{"query": "q", "expected_scenario_ids": []}])
    retrieval = AsyncMock()
    kb_scorer = AsyncMock()

    with pytest.raises(ValueError, match="agent_id"):
        await RunScenarioCasesStep(retrieval, kb_scorer).run(ctx)


# ── RunOutputGuardrailCasesStep ────────────────────────────────────────────────


_OUTPUT_SCREENING_PATH = (
    "ai.src.application.chat_evaluation.steps.run_output_guardrail_cases.apply_output_screening"
)


def _output_screening(status: str, violation_category=None, blocked_reason=None):
    from ai.src.infrastructure.chat_system.v1.guardrails.output_screening import (
        AppliedOutputScreening,
    )

    return AppliedOutputScreening(
        status=status,
        message_to_user="msg",
        original_message=None,
        blocked_reason=blocked_reason,
        violation_category=violation_category,
        screening=None,
        updated_message_history=(),
    )


@pytest.mark.asyncio
async def test_output_guardrail_pass_case_correct() -> None:
    from ai.src.application.chat_evaluation.steps.run_output_guardrail_cases import (
        RunOutputGuardrailCasesStep,
    )

    ctx = _ctx(
        eval_mode=EvalMode.OUTPUT_GUARDRAIL,
        test_cases=[{
            "query": "track my transfer",
            "assistant_message": "Your transfer is processing.",
            "expected_action": "pass",
        }],
    )
    with patch(_OUTPUT_SCREENING_PATH, new=AsyncMock(return_value=_output_screening("pass"))):
        await RunOutputGuardrailCasesStep().run(ctx)

    result = ctx.results[0]
    assert result.correct is True
    assert result.actual_status == "pass"
    assert result.expected_action == "pass"


@pytest.mark.asyncio
async def test_output_guardrail_block_case_correct() -> None:
    from ai.src.application.chat_evaluation.steps.run_output_guardrail_cases import (
        RunOutputGuardrailCasesStep,
    )

    ctx = _ctx(
        eval_mode=EvalMode.OUTPUT_GUARDRAIL,
        test_cases=[{
            "query": "what is my account number",
            "assistant_message": "Your account number is 1234567890.",
            "expected_action": "block",
        }],
    )
    with patch(_OUTPUT_SCREENING_PATH, new=AsyncMock(return_value=_output_screening("block", violation_category="pii_exposure"))):
        await RunOutputGuardrailCasesStep().run(ctx)

    result = ctx.results[0]
    assert result.correct is True
    assert result.violation_category == "pii_exposure"


@pytest.mark.asyncio
async def test_output_guardrail_reformat_case_correct() -> None:
    from ai.src.application.chat_evaluation.steps.run_output_guardrail_cases import (
        RunOutputGuardrailCasesStep,
    )

    ctx = _ctx(
        eval_mode=EvalMode.OUTPUT_GUARDRAIL,
        test_cases=[{
            "query": "help me",
            "assistant_message": "Your email is user@example.com.",
            "expected_action": "reformat",
        }],
    )
    with patch(_OUTPUT_SCREENING_PATH, new=AsyncMock(return_value=_output_screening("reformat"))):
        await RunOutputGuardrailCasesStep().run(ctx)

    assert ctx.results[0].correct is True


@pytest.mark.asyncio
async def test_output_guardrail_mismatch_marked_incorrect() -> None:
    from ai.src.application.chat_evaluation.steps.run_output_guardrail_cases import (
        RunOutputGuardrailCasesStep,
    )

    ctx = _ctx(
        eval_mode=EvalMode.OUTPUT_GUARDRAIL,
        test_cases=[{
            "query": "status",
            "assistant_message": "All good.",
            "expected_action": "block",
        }],
    )
    with patch(_OUTPUT_SCREENING_PATH, new=AsyncMock(return_value=_output_screening("pass"))):
        await RunOutputGuardrailCasesStep().run(ctx)

    assert ctx.results[0].correct is False


@pytest.mark.asyncio
async def test_output_guardrail_empty_cases_no_results() -> None:
    from ai.src.application.chat_evaluation.steps.run_output_guardrail_cases import (
        RunOutputGuardrailCasesStep,
    )

    ctx = _ctx(eval_mode=EvalMode.OUTPUT_GUARDRAIL, test_cases=[])
    await RunOutputGuardrailCasesStep().run(ctx)
    assert ctx.results == []


# ── RunE2ECasesStep ────────────────────────────────────────────────────────────


_E2E_INPUT_SCREEN_PATH = (
    "ai.src.application.chat_evaluation.steps.run_e2e_cases.apply_input_screening"
)
_E2E_OUTPUT_SCREEN_PATH = (
    "ai.src.application.chat_evaluation.steps.run_e2e_cases.apply_output_screening"
)
_E2E_SCENARIO_AGENT_PATH = (
    "ai.src.application.chat_evaluation.steps.run_e2e_cases.ScenarioAgent"
)
_E2E_RUNTIME_LOADER_PATH = (
    "ai.src.application.chat_evaluation.steps.run_e2e_cases.load_scenario_runtime"
)
_E2E_GRAPH_PATH = (
    "ai.src.application.chat_evaluation.steps.run_e2e_cases.compile_chat_graph"
)
_E2E_BUILD_SYSTEM_PROMPT_PATH = (
    "ai.src.application.chat_evaluation.steps.run_e2e_cases.build_system_prompt"
)
_E2E_BUILD_INITIAL_STATE_PATH = (
    "ai.src.application.chat_evaluation.steps.run_e2e_cases.build_initial_state"
)


def _make_e2e_ctx(test_cases=None):
    return _ctx(
        eval_mode=EvalMode.E2E,
        agent_id="00000000-0000-0000-0000-000000000001",
        test_cases=test_cases or [],
    )


def _pass_input_screen():
    return _screening("pass")


def _pass_output_screen():
    from ai.src.infrastructure.chat_system.v1.guardrails.output_screening import (
        AppliedOutputScreening,
    )

    return AppliedOutputScreening(
        status="pass",
        message_to_user="Afriex response",
        original_message=None,
        blocked_reason=None,
        violation_category=None,
        screening=None,
        updated_message_history=(),
    )


def _build_e2e_mocks(*, scenario_ids=("scn-1",), kb_id=None, retrieval_query=None):
    """Return a dict of mock patches for a full e2e run."""
    from ai.src.domain.chat_evaluation.entities import MetricResult

    routing = _scenario_result(scenario_ids=scenario_ids, kb_id=kb_id, retrieval_query=retrieval_query)
    scenario_agent_mock = MagicMock()
    scenario_agent_mock.run = AsyncMock(return_value=routing)

    graph_mock = MagicMock()
    graph_mock.ainvoke = AsyncMock(return_value={"assistant_message": "Afriex response", "llm_calls": 1})

    metric = MetricResult(name="answer_relevancy", score=0.9, threshold=0.7, success=True)
    scorer_mock = MagicMock()
    scorer_mock.score = AsyncMock(return_value=[metric])

    retrieval_mock = MagicMock()
    retrieval_mock.retrieve = AsyncMock(return_value=[])

    runtime_mock = MagicMock()
    runtime_mock.version_id = "ver-1"
    runtime_mock.scenarios = []
    runtime_mock.rules = []

    return {
        "routing": routing,
        "scenario_agent_mock": scenario_agent_mock,
        "graph_mock": graph_mock,
        "scorer_mock": scorer_mock,
        "retrieval_mock": retrieval_mock,
        "runtime_mock": runtime_mock,
    }


@pytest.mark.asyncio
async def test_e2e_full_pipeline_records_turn() -> None:
    from ai.src.application.chat_evaluation.steps.run_e2e_cases import RunE2ECasesStep

    ctx = _make_e2e_ctx(test_cases=[{"query": "track my transfer", "expected_answer": "Your transfer is processing."}])
    mocks = _build_e2e_mocks(scenario_ids=("scn-1",))

    with (
        patch(_E2E_RUNTIME_LOADER_PATH, new=AsyncMock(return_value=mocks["runtime_mock"])),
        patch(_E2E_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_E2E_SCENARIO_AGENT_PATH, return_value=mocks["scenario_agent_mock"]),
        patch(_E2E_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_input_screen())),
        patch(_E2E_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_E2E_BUILD_SYSTEM_PROMPT_PATH, return_value="system prompt"),
        patch(_E2E_BUILD_INITIAL_STATE_PATH, return_value={}),
    ):
        await RunE2ECasesStep(mocks["retrieval_mock"], mocks["scorer_mock"]).run(ctx)

    assert len(ctx.results) == 1
    result = ctx.results[0]
    assert result.actual_response == "Afriex response"
    assert result.input_guardrail_status == "pass"
    assert result.output_guardrail_status == "pass"
    assert result.pipeline_stopped is None
    assert any(m.name == "answer_relevancy" for m in result.metrics)


@pytest.mark.asyncio
async def test_e2e_input_guardrail_block_stops_pipeline() -> None:
    from ai.src.application.chat_evaluation.steps.run_e2e_cases import RunE2ECasesStep

    ctx = _make_e2e_ctx(test_cases=[{"query": "jailbreak", "expected_answer": "No."}])
    mocks = _build_e2e_mocks()

    with (
        patch(_E2E_RUNTIME_LOADER_PATH, new=AsyncMock(return_value=mocks["runtime_mock"])),
        patch(_E2E_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_E2E_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("block"))),
        patch(_E2E_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_E2E_BUILD_INITIAL_STATE_PATH, return_value={}),
    ):
        await RunE2ECasesStep(mocks["retrieval_mock"], mocks["scorer_mock"]).run(ctx)

    result = ctx.results[0]
    assert result.pipeline_stopped == "input_guardrail_block"
    assert result.actual_response == ""
    assert result.metrics == []
    mocks["graph_mock"].ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_e2e_kb_chunks_passed_to_scorer() -> None:
    from ai.src.application.chat_evaluation.steps.run_e2e_cases import RunE2ECasesStep
    from ai.src.domain.chat_evaluation.entities import MetricResult

    ctx = _make_e2e_ctx(test_cases=[{"query": "fee policy", "expected_answer": "0% fee."}])
    mocks = _build_e2e_mocks(kb_id="kb-1", retrieval_query="transfer fee policy")
    mocks["retrieval_mock"].retrieve = AsyncMock(return_value=[_chunk("0% fee"), _chunk("no hidden charges")])
    mocks["scorer_mock"].score = AsyncMock(return_value=[
        MetricResult(name="faithfulness", score=0.8, threshold=0.7, success=True)
    ])

    with (
        patch(_E2E_RUNTIME_LOADER_PATH, new=AsyncMock(return_value=mocks["runtime_mock"])),
        patch(_E2E_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_E2E_SCENARIO_AGENT_PATH, return_value=mocks["scenario_agent_mock"]),
        patch(_E2E_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_input_screen())),
        patch(_E2E_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_E2E_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_E2E_BUILD_INITIAL_STATE_PATH, return_value={}),
    ):
        await RunE2ECasesStep(mocks["retrieval_mock"], mocks["scorer_mock"]).run(ctx)

    result = ctx.results[0]
    assert result.chunks_retrieved == 2
    score_call_kwargs = mocks["scorer_mock"].score.call_args.kwargs
    assert score_call_kwargs["retrieval_context"] == ["0% fee", "no hidden charges"]


@pytest.mark.asyncio
async def test_e2e_retrieval_error_continues() -> None:
    from ai.src.application.chat_evaluation.steps.run_e2e_cases import RunE2ECasesStep

    ctx = _make_e2e_ctx(test_cases=[{"query": "limit", "expected_answer": "$2000."}])
    mocks = _build_e2e_mocks(kb_id="kb-1", retrieval_query="account limit")
    mocks["retrieval_mock"].retrieve = AsyncMock(side_effect=RuntimeError("Pinecone timeout"))

    with (
        patch(_E2E_RUNTIME_LOADER_PATH, new=AsyncMock(return_value=mocks["runtime_mock"])),
        patch(_E2E_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_E2E_SCENARIO_AGENT_PATH, return_value=mocks["scenario_agent_mock"]),
        patch(_E2E_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_input_screen())),
        patch(_E2E_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_E2E_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_E2E_BUILD_INITIAL_STATE_PATH, return_value={}),
    ):
        await RunE2ECasesStep(mocks["retrieval_mock"], mocks["scorer_mock"]).run(ctx)

    assert len(ctx.results) == 1
    assert ctx.results[0].chunks_retrieved == 0


@pytest.mark.asyncio
async def test_e2e_missing_agent_id_raises() -> None:
    from ai.src.application.chat_evaluation.steps.run_e2e_cases import RunE2ECasesStep

    ctx = _ctx(eval_mode=EvalMode.E2E, agent_id=None, test_cases=[])
    retrieval = AsyncMock()
    scorer = AsyncMock()

    with pytest.raises(ValueError, match="agent_id"):
        await RunE2ECasesStep(retrieval, scorer).run(ctx)


# ── GenerateConversationsStep ─────────────────────────────────────────────────

_GEN_RUNTIME_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".generate_conversations.load_scenario_runtime"
)
_GEN_AGENT_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".generate_conversations.ConversationGeneratorAgent"
)
_FORMAT_RULES_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".generate_conversations.format_rules"
)


def _make_scenario(id_: str, name: str):
    s = MagicMock()
    s.id = id_
    s.name = name
    s.description = f"Description of {name}"
    s.prompt = ""
    return s


def _make_runtime(scenarios=None, knowledge_bases=None):
    runtime = MagicMock()
    runtime.scenarios = scenarios or []
    runtime.knowledge_bases = knowledge_bases or []
    runtime.brand_config.name = "Afriex"
    return runtime


@pytest.mark.asyncio
async def test_generate_conversations_stores_into_ctx() -> None:
    from ai.src.application.chat_evaluation.steps.generate_conversations import (
        GenerateConversationsStep,
    )

    ctx = _ctx(
        eval_mode=EvalMode.CONVERSATION,
        agent_id="00000000-0000-0000-0000-000000000001",
    )
    runtime = _make_runtime(scenarios=[_make_scenario("scn-1", "Transfer Issues")])

    gen_mock = MagicMock()
    gen_mock.generate = AsyncMock(
        return_value=[
            {"persona": "frustrated_customer", "turns": [{"user": "hi", "agent_expected": "hello"}]},
            {"persona": "polite_but_persistent", "turns": [{"user": "fees?", "agent_expected": "0%"}]},
        ]
    )

    with (
        patch(_GEN_RUNTIME_PATH, new=AsyncMock(return_value=runtime)),
        patch(_GEN_AGENT_PATH, return_value=gen_mock),
        patch(_FORMAT_RULES_PATH, return_value=()),
    ):
        await GenerateConversationsStep().run(ctx)

    assert len(ctx.conversations) == 2
    assert ctx.conversations[0]["scenario_id"] == "scn-1"
    assert ctx.conversations[0]["persona"] == "frustrated_customer"
    assert len(ctx.conversations[0]["turns"]) == 1


@pytest.mark.asyncio
async def test_generate_conversations_missing_agent_id_raises() -> None:
    from ai.src.application.chat_evaluation.steps.generate_conversations import (
        GenerateConversationsStep,
    )

    ctx = _ctx(eval_mode=EvalMode.CONVERSATION, agent_id=None)
    with pytest.raises(ValueError, match="agent_id"):
        await GenerateConversationsStep().run(ctx)


@pytest.mark.asyncio
async def test_generate_conversations_generator_failure_continues() -> None:
    from ai.src.application.chat_evaluation.steps.generate_conversations import (
        GenerateConversationsStep,
    )

    ctx = _ctx(
        eval_mode=EvalMode.CONVERSATION,
        agent_id="00000000-0000-0000-0000-000000000001",
    )
    runtime = _make_runtime(scenarios=[_make_scenario("scn-1", "Fees")])

    gen_mock = MagicMock()
    gen_mock.generate = AsyncMock(side_effect=RuntimeError("LLM failed"))

    with (
        patch(_GEN_RUNTIME_PATH, new=AsyncMock(return_value=runtime)),
        patch(_GEN_AGENT_PATH, return_value=gen_mock),
        patch(_FORMAT_RULES_PATH, return_value=()),
    ):
        await GenerateConversationsStep().run(ctx)

    assert ctx.conversations == []  # no crash, empty result


@pytest.mark.asyncio
async def test_generate_conversations_caps_at_max_scenarios() -> None:
    from ai.src.application.chat_evaluation.steps.generate_conversations import (
        GenerateConversationsStep,
        _MAX_SCENARIOS,
    )

    ctx = _ctx(
        eval_mode=EvalMode.CONVERSATION,
        agent_id="00000000-0000-0000-0000-000000000001",
    )
    scenarios = [_make_scenario(f"scn-{i}", f"Scenario {i}") for i in range(10)]
    runtime = _make_runtime(scenarios=scenarios)

    gen_mock = MagicMock()
    gen_mock.generate = AsyncMock(return_value=[])

    with (
        patch(_GEN_RUNTIME_PATH, new=AsyncMock(return_value=runtime)),
        patch(_GEN_AGENT_PATH, return_value=gen_mock),
        patch(_FORMAT_RULES_PATH, return_value=()),
    ):
        await GenerateConversationsStep().run(ctx)

    assert gen_mock.generate.await_count == _MAX_SCENARIOS


# ── RunConversationCasesStep ──────────────────────────────────────────────────

_CONV_RUNTIME_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.load_scenario_runtime"
)
_CONV_SCENARIO_AGENT_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.ScenarioAgent"
)
_CONV_INPUT_SCREEN_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.apply_input_screening"
)
_CONV_OUTPUT_SCREEN_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.apply_output_screening"
)
_CONV_GRAPH_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.compile_chat_graph"
)
_CONV_BUILD_SYSTEM_PROMPT_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.build_system_prompt"
)
_CONV_BUILD_INITIAL_STATE_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.build_initial_state"
)
_CONV_FORMAT_RULES_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.format_rules"
)


def _make_conv_ctx(conversations=None, determinism_runs=1):
    ctx = _ctx(
        eval_mode=EvalMode.CONVERSATION,
        agent_id="00000000-0000-0000-0000-000000000001",
    )
    ctx.conversations = conversations or []
    ctx.determinism_runs = determinism_runs
    return ctx


def _make_conv_mocks():
    runtime = _make_runtime()
    routing = _scenario_result(scenario_ids=("scn-1",), kb_id=None)
    agent_mock = MagicMock()
    agent_mock.run = AsyncMock(return_value=routing)
    graph_mock = MagicMock()
    graph_mock.ainvoke = AsyncMock(
        return_value={"assistant_message": "Transfer is processing.", "llm_calls": 1}
    )
    scorer_mock = MagicMock()
    scorer_mock.score = AsyncMock(return_value=[])
    retrieval_mock = MagicMock()
    retrieval_mock.retrieve = AsyncMock(return_value=[])
    return {
        "runtime": runtime,
        "agent_mock": agent_mock,
        "graph_mock": graph_mock,
        "scorer_mock": scorer_mock,
        "retrieval_mock": retrieval_mock,
    }


@pytest.mark.asyncio
async def test_run_conversation_missing_agent_id_raises() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    ctx = _ctx(eval_mode=EvalMode.CONVERSATION, agent_id=None)
    ctx.conversations = [{"scenario_id": "s", "persona": "p", "turns": []}]
    retrieval = AsyncMock()
    scorer = AsyncMock()

    with pytest.raises(ValueError, match="agent_id"):
        await RunConversationCasesStep(retrieval, scorer).run(ctx)


@pytest.mark.asyncio
async def test_run_conversation_empty_conversations_no_results() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    ctx = _make_conv_ctx(conversations=[])
    mocks = _make_conv_mocks()

    with patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert ctx.results == []


@pytest.mark.asyncio
async def test_run_conversation_input_block_records_blocked_turn() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Fees",
        "persona": "frustrated_customer",
        "turns": [{"user": "DROP TABLE users;", "agent_expected": "I can help."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    mocks = _make_conv_mocks()

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("block"))),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert len(ctx.results) == 1
    result = ctx.results[0]
    assert result.turns[0].input_guardrail_status == "block"
    assert result.turns[0].agent_actual == "[blocked by input guardrail]"
    mocks["graph_mock"].ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_run_conversation_full_turn_recorded() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Transfer Issues",
        "persona": "polite_but_persistent",
        "turns": [{"user": "My transfer is delayed.", "agent_expected": "I can check that."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    mocks = _make_conv_mocks()

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert len(ctx.results) == 1
    result = ctx.results[0]
    assert result.scenario_id == "scn-1"
    assert result.persona == "polite_but_persistent"
    assert result.run_index == 0
    assert len(result.turns) == 1
    assert result.turns[0].agent_actual == "Afriex response"
    assert result.turns[0].input_guardrail_status == "pass"


@pytest.mark.asyncio
async def test_run_conversation_determinism_runs_repeats_each_conv() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Fees",
        "persona": "skeptical_user",
        "turns": [{"user": "What fees do you charge?", "agent_expected": "0%"}],
    }
    ctx = _make_conv_ctx(conversations=[conv], determinism_runs=3)
    mocks = _make_conv_mocks()

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert len(ctx.results) == 3
    assert ctx.results[0].run_index == 0
    assert ctx.results[1].run_index == 1
    assert ctx.results[2].run_index == 2


# ── LoadRealConversationsStep ─────────────────────────────────────────────────

_LOAD_REAL_SESSION_FACTORY_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".load_real_conversations.async_session_factory"
)


def _make_db_session(sessions=None, logs_by_session=None):
    """Return an async context manager mock that yields a DB session mock."""
    from contextlib import asynccontextmanager
    from unittest.mock import MagicMock

    sessions = sessions or []
    logs_by_session = logs_by_session or {}

    db = MagicMock()

    async def _execute(stmt):
        scalars_result = MagicMock()
        # Determine which table the statement selects from by checking attrs
        # We differentiate by checking if it's a session or log query via
        # inspecting the call order — simpler to use a call counter.
        return scalars_result

    @asynccontextmanager
    async def _factory():
        yield db

    return _factory, db


@pytest.mark.asyncio
async def test_load_real_conversations_missing_agent_id_raises() -> None:
    from ai.src.application.chat_evaluation.steps.load_real_conversations import (
        LoadRealConversationsStep,
    )

    ctx = _ctx(eval_mode=EvalMode.CONVERSATION, agent_id=None)
    with pytest.raises(ValueError, match="agent_id"):
        await LoadRealConversationsStep().run(ctx)


@pytest.mark.asyncio
async def test_load_real_conversations_no_sessions_leaves_ctx_empty() -> None:
    from unittest.mock import MagicMock
    from contextlib import asynccontextmanager

    from ai.src.application.chat_evaluation.steps.load_real_conversations import (
        LoadRealConversationsStep,
    )

    ctx = _ctx(eval_mode=EvalMode.CONVERSATION, agent_id="00000000-0000-0000-0000-000000000001")

    db = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    db.execute = AsyncMock(return_value=execute_result)

    @asynccontextmanager
    async def fake_factory():
        yield db

    with patch(_LOAD_REAL_SESSION_FACTORY_PATH, fake_factory):
        await LoadRealConversationsStep().run(ctx)

    assert ctx.conversations == []


@pytest.mark.asyncio
async def test_load_real_conversations_populates_ctx() -> None:
    from unittest.mock import MagicMock
    from contextlib import asynccontextmanager
    from uuid import uuid4 as _uuid4

    from ai.src.application.chat_evaluation.steps.load_real_conversations import (
        LoadRealConversationsStep,
    )

    agent_id = "00000000-0000-0000-0000-000000000001"
    ctx = _ctx(eval_mode=EvalMode.CONVERSATION, agent_id=agent_id)
    ctx.sample_size = 5

    session_id = _uuid4()
    session = MagicMock()
    session.id = session_id

    log_user = MagicMock()
    log_user.speaker = "user"
    log_user.content = "I need a refund"

    log_agent = MagicMock()
    log_agent.speaker = "agent"
    log_agent.content = "I can help with that"

    db = MagicMock()
    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        scalars_mock = MagicMock()
        if call_count == 0:
            scalars_mock.all.return_value = [session]
        else:
            scalars_mock.all.return_value = [log_user, log_agent]
        call_count += 1
        result = MagicMock()
        result.scalars.return_value = scalars_mock
        return result

    db.execute = _execute

    @asynccontextmanager
    async def fake_factory():
        yield db

    with patch(_LOAD_REAL_SESSION_FACTORY_PATH, fake_factory):
        await LoadRealConversationsStep().run(ctx)

    assert len(ctx.conversations) == 1
    conv = ctx.conversations[0]
    assert conv["scenario_id"] == str(session_id)
    assert conv["persona"] == "real_customer"
    # only the user turn should appear
    assert len(conv["turns"]) == 1
    assert conv["turns"][0]["user"] == "I need a refund"


@pytest.mark.asyncio
async def test_load_real_conversations_skips_sessions_with_no_user_turns() -> None:
    from unittest.mock import MagicMock
    from contextlib import asynccontextmanager
    from uuid import uuid4 as _uuid4

    from ai.src.application.chat_evaluation.steps.load_real_conversations import (
        LoadRealConversationsStep,
    )

    ctx = _ctx(eval_mode=EvalMode.CONVERSATION, agent_id="00000000-0000-0000-0000-000000000001")

    session = MagicMock()
    session.id = _uuid4()

    log_agent_only = MagicMock()
    log_agent_only.speaker = "agent"
    log_agent_only.content = "Hello!"

    db = MagicMock()
    call_count = 0

    async def _execute(stmt):
        nonlocal call_count
        scalars_mock = MagicMock()
        if call_count == 0:
            scalars_mock.all.return_value = [session]
        else:
            scalars_mock.all.return_value = [log_agent_only]
        call_count += 1
        result = MagicMock()
        result.scalars.return_value = scalars_mock
        return result

    db.execute = _execute

    @asynccontextmanager
    async def fake_factory():
        yield db

    with patch(_LOAD_REAL_SESSION_FACTORY_PATH, fake_factory):
        await LoadRealConversationsStep().run(ctx)

    assert ctx.conversations == []


# ── Stub pipeline steps ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_termination_step_raises_not_implemented() -> None:
    from ai.src.application.chat_evaluation.steps.check_termination import (
        CheckTerminationStep,
    )
    with pytest.raises(NotImplementedError):
        await CheckTerminationStep().run(None)


@pytest.mark.asyncio
async def test_persist_result_step_raises_not_implemented() -> None:
    from ai.src.application.chat_evaluation.steps.persist_result import (
        PersistResultStep,
    )
    with pytest.raises(NotImplementedError):
        await PersistResultStep().run(None)


@pytest.mark.asyncio
async def test_run_agent_turn_step_raises_not_implemented() -> None:
    from ai.src.application.chat_evaluation.steps.run_agent_turn import (
        RunAgentTurnStep,
    )
    with pytest.raises(NotImplementedError):
        await RunAgentTurnStep().run(None)


@pytest.mark.asyncio
async def test_initialise_conversation_step_raises_not_implemented() -> None:
    from ai.src.application.chat_evaluation.steps.initialise_conversation import (
        InitialiseConversationStep,
    )
    with pytest.raises(NotImplementedError):
        await InitialiseConversationStep().run(None)


@pytest.mark.asyncio
async def test_load_evaluation_config_step_raises_not_implemented() -> None:
    from ai.src.application.chat_evaluation.steps.load_evaluation_config import (
        LoadEvaluationConfigStep,
    )
    with pytest.raises(NotImplementedError):
        await LoadEvaluationConfigStep().run(None)


@pytest.mark.asyncio
async def test_run_simulated_user_turn_step_raises_not_implemented() -> None:
    from ai.src.application.chat_evaluation.steps.run_simulated_user_turn import (
        RunSimulatedUserTurnStep,
    )
    with pytest.raises(NotImplementedError):
        await RunSimulatedUserTurnStep().run(None)


@pytest.mark.asyncio
async def test_score_with_judge_skips_when_no_criteria() -> None:
    from ai.src.application.chat_evaluation.steps.score_with_judge import (
        ScoreWithJudgeStep,
    )

    ctx = _ctx(eval_mode=EvalMode.CONVERSATION)
    ctx.judge_criteria = []
    agent_mock = MagicMock()
    agent_mock.score = AsyncMock()
    await ScoreWithJudgeStep(agent=agent_mock).run(ctx)

    agent_mock.score.assert_not_called()


@pytest.mark.asyncio
async def test_score_with_judge_populates_judge_scores_on_results() -> None:
    from ai.src.application.chat_evaluation.steps.score_with_judge import (
        ScoreWithJudgeStep,
    )
    from ai.src.domain.chat_evaluation.entities import (
        ConversationCaseResult,
        ConversationTurn,
    )

    turn = ConversationTurn(
        user="Where is my money?",
        agent_expected="I'll check.",
        agent_actual="I'll look into that now.",
        input_guardrail_status="pass",
        output_guardrail_status="pass",
    )
    result = ConversationCaseResult(
        scenario_id="scn-1",
        scenario_name="Transfer",
        persona="frustrated_customer",
        run_index=0,
        turns=[turn],
    )

    ctx = _ctx(eval_mode=EvalMode.CONVERSATION)
    ctx.judge_criteria = ["Agent acknowledged the customer's issue."]
    ctx.results = [result]

    agent_mock = MagicMock()
    agent_mock.score = AsyncMock(
        return_value={
            "Agent acknowledged the customer's issue.": {
                "score": 0.9,
                "reason": "Agent responded promptly.",
            }
        }
    )

    await ScoreWithJudgeStep(agent=agent_mock).run(ctx)

    agent_mock.score.assert_awaited_once()
    assert result.judge_scores == {
        "Agent acknowledged the customer's issue.": {
            "score": 0.9,
            "reason": "Agent responded promptly.",
        }
    }


@pytest.mark.asyncio
async def test_score_with_judge_skips_results_with_no_turns() -> None:
    from ai.src.application.chat_evaluation.steps.score_with_judge import (
        ScoreWithJudgeStep,
    )
    from ai.src.domain.chat_evaluation.entities import ConversationCaseResult

    empty_result = ConversationCaseResult(
        scenario_id="scn-1",
        scenario_name="Fees",
        persona="user",
        run_index=0,
        turns=[],
    )
    ctx = _ctx(eval_mode=EvalMode.CONVERSATION)
    ctx.judge_criteria = ["Some criterion"]
    ctx.results = [empty_result]

    agent_mock = MagicMock()
    agent_mock.score = AsyncMock()
    await ScoreWithJudgeStep(agent=agent_mock).run(ctx)

    agent_mock.score.assert_not_called()
    assert empty_result.judge_scores == {}


@pytest.mark.asyncio
async def test_score_with_judge_continues_on_agent_exception() -> None:
    from ai.src.application.chat_evaluation.steps.score_with_judge import (
        ScoreWithJudgeStep,
    )
    from ai.src.domain.chat_evaluation.entities import (
        ConversationCaseResult,
        ConversationTurn,
    )

    turn = ConversationTurn(
        user="Help",
        agent_expected="Sure.",
        agent_actual="Sure.",
        input_guardrail_status="pass",
        output_guardrail_status="pass",
    )
    result = ConversationCaseResult(
        scenario_id="scn-1",
        scenario_name="Fees",
        persona="user",
        run_index=0,
        turns=[turn],
    )
    ctx = _ctx(eval_mode=EvalMode.CONVERSATION)
    ctx.judge_criteria = ["A criterion"]
    ctx.results = [result]

    agent_mock = MagicMock()
    agent_mock.score = AsyncMock(side_effect=RuntimeError("LLM timeout"))

    await ScoreWithJudgeStep(agent=agent_mock).run(ctx)

    assert result.judge_scores == {}  # no crash, score stays empty


# ── LabelExpectedScenariosStep ─────────────────────────────────────────────────

_LABEL_RUNTIME_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".label_expected_scenarios.load_scenario_runtime"
)


@pytest.mark.asyncio
async def test_label_step_raises_when_no_agent_id() -> None:
    from ai.src.application.chat_evaluation.steps.label_expected_scenarios import (
        LabelExpectedScenariosStep,
    )
    ctx = _ctx(agent_id=None)
    with pytest.raises(ValueError, match="agent_id"):
        await LabelExpectedScenariosStep().run(ctx)


@pytest.mark.asyncio
async def test_label_step_skips_already_labelled_cases() -> None:
    from ai.src.application.chat_evaluation.steps.label_expected_scenarios import (
        LabelExpectedScenariosStep,
    )
    tc = {"query": "hi", "expected_scenario_ids": ["scn-1"]}
    ctx = _ctx(agent_id="00000000-0000-0000-0000-000000000001", test_cases=[tc])

    runtime = MagicMock()
    runtime.scenarios = []
    judge = MagicMock()
    judge.label = AsyncMock()

    with patch(_LABEL_RUNTIME_PATH, new=AsyncMock(return_value=runtime)):
        await LabelExpectedScenariosStep(judge=judge).run(ctx)

    judge.label.assert_not_called()
    assert tc["expected_scenario_ids"] == ["scn-1"]


@pytest.mark.asyncio
async def test_label_step_auto_labels_unlabelled_cases() -> None:
    from ai.src.application.chat_evaluation.steps.label_expected_scenarios import (
        LabelExpectedScenariosStep,
    )
    tc = {"query": "transfer stuck", "expected_scenario_ids": []}
    ctx = _ctx(agent_id="00000000-0000-0000-0000-000000000001", test_cases=[tc])

    scenario = MagicMock()
    scenario.id = "scn-transfer"
    scenario.name = "Transfer Issues"
    scenario.description = "Handles delayed transfers"
    runtime = MagicMock()
    runtime.scenarios = [scenario]

    judge = MagicMock()
    judge.label = AsyncMock(return_value=(["scn-transfer"], "clear match"))

    with patch(_LABEL_RUNTIME_PATH, new=AsyncMock(return_value=runtime)):
        await LabelExpectedScenariosStep(judge=judge).run(ctx)

    assert tc["expected_scenario_ids"] == ["scn-transfer"]
    assert tc["_judge_labelled"] is True
    assert tc["_judge_reason"] == "clear match"
    assert ctx.scenarios_catalog == [
        ("scn-transfer", "Transfer Issues", "Handles delayed transfers")
    ]


@pytest.mark.asyncio
async def test_label_step_catalog_uses_empty_string_for_none_description() -> None:
    from ai.src.application.chat_evaluation.steps.label_expected_scenarios import (
        LabelExpectedScenariosStep,
    )
    ctx = _ctx(agent_id="00000000-0000-0000-0000-000000000001", test_cases=[])

    scenario = MagicMock()
    scenario.id = "scn-1"
    scenario.name = "Fees"
    scenario.description = None
    runtime = MagicMock()
    runtime.scenarios = [scenario]

    with patch(_LABEL_RUNTIME_PATH, new=AsyncMock(return_value=runtime)):
        await LabelExpectedScenariosStep(judge=MagicMock()).run(ctx)

    assert ctx.scenarios_catalog == [("scn-1", "Fees", "")]


# ── RunConversationCasesStep: scorer exception path ───────────────────────────


@pytest.mark.asyncio
async def test_run_conversation_scorer_exception_records_fallback_metric() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )
    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Fees",
        "persona": "skeptical_user",
        "turns": [{"user": "What fees?", "agent_expected": "Zero."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    mocks = _make_conv_mocks()
    mocks["scorer_mock"].score = AsyncMock(side_effect=RuntimeError("GEval timeout"))

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(
            _CONV_OUTPUT_SCREEN_PATH,
            new=AsyncMock(return_value=_pass_output_screen()),
        ),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert len(ctx.results) == 1
    assert ctx.results[0].scores.get("conversation_quality") == 0.0


@pytest.mark.asyncio
async def test_run_conversation_skips_turn_with_empty_user_message() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Fees",
        "persona": "user",
        "turns": [
            {"user": "   ", "agent_expected": "ignored"},
            {"user": "What fees?", "agent_expected": "Zero."},
        ],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    mocks = _make_conv_mocks()

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert len(ctx.results) == 1
    assert len(ctx.results[0].turns) == 1


@pytest.mark.asyncio
async def test_run_conversation_retrieval_query_calls_retrieve_and_formats_kb() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-kb",
        "scenario_name": "Fees KB",
        "persona": "user",
        "turns": [{"user": "What is the fee?", "agent_expected": "Zero."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    mocks = _make_conv_mocks()

    chunk = MagicMock()
    chunk.text = "Fee policy: no fees."
    mocks["retrieval_mock"].retrieve = AsyncMock(return_value=[chunk])

    routing_with_query = _scenario_result(
        scenario_ids=("scn-kb",), retrieval_query="fee policy"
    )
    mocks["agent_mock"].run = AsyncMock(return_value=routing_with_query)

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    mocks["retrieval_mock"].retrieve.assert_called_once()
    assert len(ctx.results) == 1


_CONV_LOAD_TOOLS_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.load_agent_tools"
)
_CONV_LOAD_TOOLS_WITH_MOCKS_PATH = (
    "ai.src.application.chat_evaluation.steps"
    ".run_conversation_cases.load_agent_tools_with_mocks"
)


@pytest.mark.asyncio
async def test_run_conversation_first_speaker_agent_preseeds_welcome_message() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Greeting",
        "persona": "calm_detailed",
        "turns": [{"user": "Hello there", "agent_expected": "Welcome!"}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    ctx.first_speaker = "agent"
    ctx.welcome_message = "Hi! How can I help you today?"
    mocks = _make_conv_mocks()

    captured_states: list[dict] = []

    def _capture_state(**kwargs):
        captured_states.append(kwargs)
        return {}

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, side_effect=_capture_state),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert len(captured_states) == 1
    history = captured_states[0]["message_history"]
    assert len(history) == 1
    assert history[0].role.value == "assistant"
    assert history[0].content == "Hi! How can I help you today?"


@pytest.mark.asyncio
async def test_run_conversation_first_speaker_human_sim_no_preseed() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Fees",
        "persona": "user",
        "turns": [{"user": "What fees?", "agent_expected": "Zero."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    ctx.first_speaker = "human_sim"
    ctx.welcome_message = "This message should not appear."
    mocks = _make_conv_mocks()

    captured_states: list[dict] = []

    def _capture_state(**kwargs):
        captured_states.append(kwargs)
        return {}

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, side_effect=_capture_state),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert len(captured_states) == 1
    history = captured_states[0]["message_history"]
    assert len(history) == 0


@pytest.mark.asyncio
async def test_run_conversation_api_tool_mocks_uses_mock_loader() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Tools",
        "persona": "user",
        "turns": [{"user": "Check my balance.", "agent_expected": "Sure."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    ctx.api_tool_mocks = {"get_customer": {"id": "cus_1"}}
    mocks = _make_conv_mocks()

    mock_tool = MagicMock()
    mock_tool.name = "get_customer"

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_LOAD_TOOLS_WITH_MOCKS_PATH, return_value=[mock_tool]) as mock_loader,
        patch(_CONV_LOAD_TOOLS_PATH) as real_loader,
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    mock_loader.assert_called_once()
    real_loader.assert_not_called()


@pytest.mark.asyncio
async def test_run_conversation_no_api_tool_mocks_uses_real_loader() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Tools",
        "persona": "user",
        "turns": [{"user": "What fees?", "agent_expected": "Zero."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    ctx.api_tool_mocks = {}
    mocks = _make_conv_mocks()

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_LOAD_TOOLS_PATH, return_value=[]) as real_loader,
        patch(_CONV_LOAD_TOOLS_WITH_MOCKS_PATH) as mock_loader,
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    real_loader.assert_called_once()
    mock_loader.assert_not_called()


@pytest.mark.asyncio
async def test_run_conversation_retrieval_exception_uses_empty_chunks() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-err",
        "scenario_name": "KB Error",
        "persona": "user",
        "turns": [{"user": "Hello?", "agent_expected": "Hi."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    mocks = _make_conv_mocks()
    mocks["retrieval_mock"].retrieve = AsyncMock(side_effect=RuntimeError("pinecone down"))

    routing_with_query = _scenario_result(
        scenario_ids=("scn-err",), retrieval_query="something"
    )
    mocks["agent_mock"].run = AsyncMock(return_value=routing_with_query)

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(_CONV_INPUT_SCREEN_PATH, new=AsyncMock(return_value=_screening("pass"))),
        patch(_CONV_OUTPUT_SCREEN_PATH, new=AsyncMock(return_value=_pass_output_screen())),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert len(ctx.results) == 1


@pytest.mark.asyncio
async def test_run_conversation_task_exception_skipped_in_gather() -> None:
    from ai.src.application.chat_evaluation.steps.run_conversation_cases import (
        RunConversationCasesStep,
    )

    conv = {
        "scenario_id": "scn-1",
        "scenario_name": "Fees",
        "persona": "user",
        "turns": [{"user": "What fees?", "agent_expected": "Zero."}],
    }
    ctx = _make_conv_ctx(conversations=[conv])
    mocks = _make_conv_mocks()

    with (
        patch(_CONV_RUNTIME_PATH, new=AsyncMock(return_value=mocks["runtime"])),
        patch(_CONV_GRAPH_PATH, return_value=mocks["graph_mock"]),
        patch(_CONV_SCENARIO_AGENT_PATH, return_value=mocks["agent_mock"]),
        patch(
            _CONV_INPUT_SCREEN_PATH,
            new=AsyncMock(side_effect=RuntimeError("screening crashed")),
        ),
        patch(_CONV_BUILD_SYSTEM_PROMPT_PATH, return_value="sp"),
        patch(_CONV_BUILD_INITIAL_STATE_PATH, return_value={}),
        patch(_CONV_FORMAT_RULES_PATH, return_value=()),
    ):
        await RunConversationCasesStep(
            mocks["retrieval_mock"], mocks["scorer_mock"]
        ).run(ctx)

    assert ctx.results == []
