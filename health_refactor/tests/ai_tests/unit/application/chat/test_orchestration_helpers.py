"""Unit tests: application/chat/orchestration_helpers.py"""
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from ai.src.application.chat.orchestration_helpers import (
    build_system_prompt,
    format_rules,
    orchestration_trace,
    scenario_prompt_for,
    scenarios_prompt_for,
    tool_calls_summary,
)
from backend.src.infrastructure.agent_runtime.types import (
    AgentRuntimeContext,
    DEFAULT_RUNTIME_BRAND,
    DEFAULT_RUNTIME_PERSONALIZATION,
    RuntimeContextItem,
    ScenarioRuntimeItem,
)

SCENARIO_ID = UUID("00000000-0000-4000-8000-000000000010")
SCENARIO_ID_2 = UUID("00000000-0000-4000-8000-000000000011")


def _runtime() -> AgentRuntimeContext:
    return AgentRuntimeContext(
        agent_id=uuid4(),
        organization_id=uuid4(),
        version_id=uuid4(),
        version_number=1,
        agent_name="Support Bot",
        brand_config=DEFAULT_RUNTIME_BRAND,
        personalization_config=DEFAULT_RUNTIME_PERSONALIZATION,
        scenarios=(
            ScenarioRuntimeItem(
                id=SCENARIO_ID,
                name="Refund",
                description="Refund flow",
                prompt="Verify the order number.",
            ),
            ScenarioRuntimeItem(
                id=SCENARIO_ID_2,
                name="Account update",
                description="Change account details",
                prompt="Verify identity before changes.",
            ),
        ),
        rules=(
            RuntimeContextItem(
                id=uuid4(),
                name="Privacy",
                description="Never ask for passwords.",
            ),
            RuntimeContextItem(
                id=uuid4(),
                name="Empty",
                description="",
            ),
        ),
        knowledge_bases=(),
    )


def test_format_rules_includes_all_configured_rules() -> None:
    runtime = _runtime()

    rules = format_rules(runtime)

    assert rules == (
        "Privacy: Never ask for passwords.",
        "Empty",
    )


def test_scenario_prompt_for_returns_matching_prompt() -> None:
    runtime = _runtime()

    prompt = scenario_prompt_for(runtime, str(SCENARIO_ID))

    assert prompt == "Scenario: Refund\nVerify the order number."


def test_scenario_prompt_for_returns_none_when_missing() -> None:
    runtime = _runtime()

    assert scenario_prompt_for(runtime, None) is None
    assert scenario_prompt_for(runtime, str(uuid4())) is None


def test_scenarios_prompt_for_merges_multiple_scenarios() -> None:
    runtime = _runtime()

    prompt = scenarios_prompt_for(
        runtime,
        (str(SCENARIO_ID), str(SCENARIO_ID_2)),
    )

    assert prompt is not None
    assert "Scenario: Refund" in prompt
    assert "Verify the order number." in prompt
    assert "Scenario: Account update" in prompt
    assert "Verify identity before changes." in prompt


def test_build_system_prompt_includes_agent_name() -> None:
    runtime = _runtime()

    prompt = build_system_prompt(
        runtime,
        scenario_prompt="Handle refunds.",
        rules=format_rules(runtime),
        knowledge_base_context=None,
        tool_names=("lookup_order",),
        session_conversation_state="in_progress",
    )

    assert "Support Bot" in prompt
    assert "Handle refunds." in prompt
    assert "lookup_order" in prompt
    assert "Configured agent rules:" in prompt
    assert "Privacy: Never ask for passwords." in prompt


def test_tool_calls_summary_collects_calls_and_results() -> None:
    messages = [
        AIMessage(
            content="",
            tool_calls=[{"name": "lookup_order", "args": {"id": "1"}, "id": "call-1"}],
        ),
        ToolMessage(content="Order found", tool_call_id="call-1"),
    ]

    summary = tool_calls_summary(messages)

    assert summary == [
        {"name": "lookup_order", "args": {"id": "1"}},
        {"tool_result": "Order found"},
    ]


def test_orchestration_trace_maps_message_types() -> None:
    raw = '{"message": "Hello there", "conversation_state": "in_progress"}'
    messages = [
        SystemMessage(content="You are helpful."),
        HumanMessage(content="Hi"),
        AIMessage(content=raw),
        AIMessage(
            content="",
            tool_calls=[{"name": "lookup", "args": {}, "id": "call-1"}],
        ),
        ToolMessage(content="done", tool_call_id="call-1"),
    ]

    trace = orchestration_trace(messages, preview_chars=50)

    assert trace[0]["step"] == "system_prompt"
    assert trace[1]["step"] == "history_or_user"
    assert trace[2]["step"] == "llm_turn"
    assert trace[2]["turn"] == 1
    assert trace[2]["parse_success"] is True
    assert trace[3]["step"] == "llm_turn"
    assert trace[3]["tool_calls"] == [{"name": "lookup", "args": {}}]
    assert trace[4]["step"] == "tool_result"
