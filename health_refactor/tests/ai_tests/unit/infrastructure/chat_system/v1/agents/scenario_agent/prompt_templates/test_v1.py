"""Unit tests: scenario agent prompt template v1."""
from ai.src.domain.chat_system.v1.types import (
    CurrentKnowledgeBase,
    CurrentScenario,
    ScenarioContextOption,
)
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.prompt_templates import v1


def test_build_system_prompt_lists_scenarios_and_knowledge_bases() -> None:
    ctx = v1.PromptContext(
        user_query="refund please",
        message_history=(),
        current_scenario=None,
        current_knowledge_base=None,
        scenarios=(
            ScenarioContextOption(
                id="scenario-1",
                name="Refund",
                description="Refund requests",
            ),
        ),
        knowledge_bases=(
            ScenarioContextOption(
                id="kb-1",
                name="Refund FAQ",
                description="Policy docs",
            ),
        ),
    )

    prompt = v1.build_system_prompt(ctx)

    assert "scenario-1" in prompt
    assert "title=Refund FAQ" in prompt
    assert "retrieval_query" in prompt
    assert "experience_queries" in prompt
    assert "rule_ids" not in prompt


def test_build_user_prompt_includes_latest_message() -> None:
    ctx = v1.PromptContext(
        user_query="I need help",
        message_history=(),
        current_scenario=None,
        current_knowledge_base=None,
        scenarios=(),
        knowledge_bases=(),
    )

    prompt = v1.build_user_prompt(ctx)

    assert "I need help" in prompt


def test_build_system_prompt_shows_current_scenario_when_set() -> None:
    ctx = v1.PromptContext(
        user_query="what is the status?",
        message_history=(),
        current_scenario=CurrentScenario(
            title="Refund request",
            description="Customer wants a refund.",
        ),
        current_knowledge_base=None,
        scenarios=(),
        knowledge_bases=(),
    )

    prompt = v1.build_system_prompt(ctx)

    assert "title: Refund request" in prompt
    assert "description: Customer wants a refund." in prompt


def test_build_system_prompt_shows_current_knowledge_base_when_set() -> None:
    ctx = v1.PromptContext(
        user_query="what is the policy?",
        message_history=(),
        current_scenario=None,
        current_knowledge_base=CurrentKnowledgeBase(
            title="Refund FAQ",
            description="Refund policy articles.",
        ),
        scenarios=(),
        knowledge_bases=(),
    )

    prompt = v1.build_system_prompt(ctx)

    assert "title: Refund FAQ" in prompt
    assert "description: Refund policy articles." in prompt


def test_build_system_prompt_shows_none_when_no_current_context() -> None:
    ctx = v1.PromptContext(
        user_query="hello",
        message_history=(),
        current_scenario=None,
        current_knowledge_base=None,
        scenarios=(),
        knowledge_bases=(),
    )

    prompt = v1.build_system_prompt(ctx)

    assert "Current active scenario: none" in prompt
    assert "Current active knowledge base: none" in prompt


def test_build_system_prompt_includes_current_datetime_context() -> None:
    ctx = v1.PromptContext(
        user_query="hello",
        message_history=(),
        current_scenario=None,
        current_knowledge_base=None,
        scenarios=(),
        knowledge_bases=(),
        timezone="Africa/Lagos",
    )

    prompt = v1.build_system_prompt(ctx)

    assert "Session context:" in prompt
    assert "Current date and time (Africa/Lagos):" in prompt


def test_output_format_defines_routing_shape() -> None:
    assert '"scenario_ids"' in v1.OUTPUT_FORMAT.template
    assert '"knowledge_base_id"' in v1.OUTPUT_FORMAT.template
    assert '"rule_ids"' not in v1.OUTPUT_FORMAT.template
    assert '"retrieval_query"' in v1.OUTPUT_FORMAT.template
    assert '"experience_queries"' in v1.OUTPUT_FORMAT.template
