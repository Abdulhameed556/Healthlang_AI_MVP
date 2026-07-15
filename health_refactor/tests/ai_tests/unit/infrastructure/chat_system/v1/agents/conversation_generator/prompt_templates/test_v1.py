"""Unit tests: conversation generator agent prompt template v1."""


def test_output_format_is_defined() -> None:
    from ai.src.infrastructure.chat_system.v1.agents.conversation_generator.prompt_templates.v1 import (
        OUTPUT_FORMAT,
    )
    from ai.src.domain.llm.json_format import JsonOutputFormat

    assert isinstance(OUTPUT_FORMAT, JsonOutputFormat)


def test_build_system_prompt_contains_persona_descriptions() -> None:
    from ai.src.infrastructure.chat_system.v1.agents.conversation_generator.prompt_templates.v1 import (
        PromptContext,
        build_system_prompt,
    )

    ctx = PromptContext(
        agent_name="Afriex Support",
        scenario_name="Transfer Issues",
        scenario_description="Handle delayed transfers",
        scenario_prompt="Empathise with the customer.",
        persona_1="frustrated_customer",
        persona_2="polite_but_persistent",
        knowledge_bases=[{"name": "Afriex FAQ", "description": "Product docs"}],
        rules=["Never share PINs", "Respond in English"],
    )
    prompt = build_system_prompt(ctx)

    assert "frustrated_customer" in prompt
    assert "polite_but_persistent" in prompt
    assert "Transfer Issues" in prompt
    assert "Never share PINs" in prompt
    assert "Afriex FAQ" in prompt


def test_build_system_prompt_handles_empty_kb_and_rules() -> None:
    from ai.src.infrastructure.chat_system.v1.agents.conversation_generator.prompt_templates.v1 import (
        PromptContext,
        build_system_prompt,
    )

    ctx = PromptContext(
        agent_name="Agent",
        scenario_name="Fees",
        scenario_description="Fee queries",
        scenario_prompt="",
        persona_1="skeptical_user",
        persona_2="calm_detailed",
        knowledge_bases=[],
        rules=[],
    )
    prompt = build_system_prompt(ctx)

    assert "none configured" in prompt


def test_build_user_prompt_includes_scenario_and_personas() -> None:
    from ai.src.infrastructure.chat_system.v1.agents.conversation_generator.prompt_templates.v1 import (
        PromptContext,
        build_user_prompt,
    )

    ctx = PromptContext(
        agent_name="Agent",
        scenario_name="Account Verification",
        scenario_description="Verify identity",
        scenario_prompt="",
        persona_1="confused_first_timer",
        persona_2="calm_detailed",
    )
    prompt = build_user_prompt(ctx)

    assert "Account Verification" in prompt
    assert "confused_first_timer" in prompt
    assert "calm_detailed" in prompt


def test_persona_descriptions_cover_all_five() -> None:
    from ai.src.infrastructure.chat_system.v1.agents.conversation_generator.prompt_templates.v1 import (
        PERSONA_DESCRIPTIONS,
    )

    expected = {
        "frustrated_customer",
        "confused_first_timer",
        "polite_but_persistent",
        "skeptical_user",
        "calm_detailed",
    }
    assert set(PERSONA_DESCRIPTIONS.keys()) == expected
