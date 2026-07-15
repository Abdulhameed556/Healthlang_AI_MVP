"""Unit tests: conversation generator prompt template v1."""
from ai.src.infrastructure.chat_system.v1.agents.conversation_generator.prompt_templates.v1 import (  # noqa: E501
    PromptContext,
    _format_agent_variables,
    build_system_prompt,
    build_user_prompt,
)


def _base_ctx(**kwargs) -> PromptContext:
    defaults = dict(
        agent_name="Support Bot",
        scenario_name="Transfer Issues",
        scenario_description="Handle delayed transfers",
        scenario_prompt="",
        persona_1="frustrated_customer",
        persona_2="calm_detailed",
    )
    defaults.update(kwargs)
    return PromptContext(**defaults)


# ── _format_agent_variables ───────────────────────────────────────────────────


def test_format_agent_variables_empty_returns_placeholder() -> None:
    assert _format_agent_variables({}) == "  (none provided)"


def test_format_agent_variables_single_entry() -> None:
    result = _format_agent_variables({"customer_id": "cus_123"})
    assert result == "  customer_id: cus_123"


def test_format_agent_variables_multiple_entries() -> None:
    result = _format_agent_variables(
        {"customer_id": "cus_123", "support_tier": "Enterprise Gold"}
    )
    assert "  customer_id: cus_123" in result
    assert "  support_tier: Enterprise Gold" in result


# ── build_system_prompt: agent_variables block ────────────────────────────────


def test_system_prompt_omits_customer_context_when_no_variables() -> None:
    ctx = _base_ctx()
    prompt = build_system_prompt(ctx)
    assert "Customer context for this session" not in prompt


def test_system_prompt_includes_customer_context_when_variables_set() -> None:
    ctx = _base_ctx(
        agent_variables={"customer_id": "cus_123", "support_tier": "Gold"}
    )
    prompt = build_system_prompt(ctx)
    assert "Customer context for this session:" in prompt
    assert "customer_id: cus_123" in prompt
    assert "support_tier: Gold" in prompt


def test_system_prompt_includes_do_not_announce_instruction() -> None:
    ctx = _base_ctx(agent_variables={"support_tier": "Gold"})
    prompt = build_system_prompt(ctx)
    assert "do not announce them directly" in prompt


# ── build_system_prompt: core content ─────────────────────────────────────────


def test_system_prompt_includes_scenario_name() -> None:
    ctx = _base_ctx(scenario_name="KYC Verification")
    assert "KYC Verification" in build_system_prompt(ctx)


def test_system_prompt_includes_agent_name() -> None:
    ctx = _base_ctx(agent_name="Aria")
    assert "Aria" in build_system_prompt(ctx)


def test_system_prompt_includes_conversation_rounds() -> None:
    ctx = _base_ctx(conversation_rounds=7)
    assert "7 turns" in build_system_prompt(ctx)


def test_system_prompt_includes_rules() -> None:
    ctx = _base_ctx(rules=["Never share PINs", "Stay on topic"])
    prompt = build_system_prompt(ctx)
    assert "Never share PINs" in prompt
    assert "Stay on topic" in prompt


def test_system_prompt_includes_knowledge_bases() -> None:
    ctx = _base_ctx(
        knowledge_bases=[{"name": "Afriex FAQ", "description": "Product docs"}]
    )
    assert "Afriex FAQ" in build_system_prompt(ctx)


def test_system_prompt_includes_both_personas() -> None:
    ctx = _base_ctx(
        persona_1="frustrated_customer", persona_2="skeptical_user"
    )
    prompt = build_system_prompt(ctx)
    assert "frustrated_customer" in prompt
    assert "skeptical_user" in prompt


def test_system_prompt_uses_standard_handling_when_no_scenario_prompt() -> None:
    ctx = _base_ctx(scenario_prompt="")
    assert "(standard handling)" in build_system_prompt(ctx)


def test_system_prompt_uses_custom_scenario_prompt_when_set() -> None:
    ctx = _base_ctx(scenario_prompt="Always escalate after 2 attempts.")
    assert "Always escalate after 2 attempts." in build_system_prompt(ctx)


# ── build_user_prompt ─────────────────────────────────────────────────────────


def test_user_prompt_includes_scenario_name_and_personas() -> None:
    ctx = _base_ctx(
        scenario_name="Fees",
        persona_1="calm_detailed",
        persona_2="skeptical_user",
    )
    prompt = build_user_prompt(ctx)
    assert "Fees" in prompt
    assert "calm_detailed" in prompt
    assert "skeptical_user" in prompt
