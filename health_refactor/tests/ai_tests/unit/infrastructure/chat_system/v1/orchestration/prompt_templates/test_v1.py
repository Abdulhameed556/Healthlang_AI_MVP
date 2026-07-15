"""Unit tests: orchestration prompt template v1."""
from backend.src.domain.agents.brand_personalization import (
    brand_config_from_dict,
    personalization_config_from_dict,
)
from ai.src.infrastructure.chat_system.v1.orchestration.prompt_templates import v1


def test_build_system_prompt_includes_brand_and_personalization() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            brand_config=brand_config_from_dict(
                {
                    "company_name": "Acme Global Solutions",
                    "languages": ["english"],
                    "identity_name": "Alex",
                    "timezone": "UTC",
                }
            ),
            personalization_config=personalization_config_from_dict(
                {
                    "tone_profile": "empathetic_professional",
                    "formality": "balanced",
                    "pacing": 1.0,
                    "custom_greeting": "Hello! Thank you for contacting Acme Support.",
                    "custom_sign_off": "Is there anything else I can assist you with?",
                    "enable_sentiment_analysis": True,
                }
            ),
        )
    )

    assert "You are Alex, the customer support assistant for Acme Global Solutions." in prompt
    assert "Acme Global Solutions" in prompt
    assert "Current date and time (UTC):" in prompt
    assert "empathetic professional" in prompt
    assert "balanced" in prompt
    assert "Hello! Thank you for contacting Acme Support." in prompt
    assert "conversation_state" in prompt
    assert "<json>" in prompt


def test_build_system_prompt_includes_scenario_rules_and_kb_context() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            scenario_prompt="Handle refund requests with empathy.",
            rules=("Never share passwords.",),
            knowledge_base_context="Refunds allowed within 30 days.",
            session_conversation_state="in_progress",
        )
    )

    assert "Handle refund requests with empathy." in prompt
    assert "Never share passwords." in prompt
    assert "Refunds allowed within 30 days." in prompt


def test_build_system_prompt_lists_conversation_state_policy() -> None:
    prompt = v1.build_system_prompt(v1.PromptContext(agent_name="Support Bot v2"))

    assert "transfer_to_live_support" in prompt
    assert "end_conversation" in prompt


def test_build_system_prompt_instructs_completed_phrasing_for_closing_states() -> None:
    prompt = v1.build_system_prompt(v1.PromptContext(agent_name="Support Bot v2"))

    # Closing states end the chat on that turn, so the model must phrase them as
    # a completed action, not a pending "please hold" one.
    assert "Message phrasing for closing states" in prompt
    assert "CLOSES the chat immediately on this turn" in prompt
    assert "COMPLETED action" in prompt
    assert "You will NOT get another turn" in prompt


def test_build_system_prompt_enforces_json_only_final_replies() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            tool_names=("get_user_v2",),
        )
    )

    assert "Response discipline (strict):" in prompt
    assert "entire assistant reply = one <json>...</json> block" in prompt
    assert "light markdown only" in prompt
    assert "Never reply with raw prose or markdown outside <json> tags" in prompt
    assert "Do not use HTML tags or code fences in message" in prompt
    assert "After tool results:" in prompt
    assert "Tool-call turns: emit tool calls only" in prompt


def test_build_system_prompt_json_discipline_without_tools() -> None:
    prompt = v1.build_system_prompt(v1.PromptContext(agent_name="Support Bot v2"))

    assert "Response discipline (strict):" in prompt
    assert "Calling tools:" not in prompt
    assert "No text, markdown fences, or commentary before or after the tags" in prompt


def test_build_system_prompt_requires_explicit_confirmation_before_end_conversation() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            personalization_config=personalization_config_from_dict(
                {"custom_sign_off": "Is there anything else I can assist you with?"}
            ),
        )
    )

    assert "NEVER use this just because you finished an answer" in prompt
    assert "your immediately previous assistant message was pending_close" in prompt
    assert "NOT end_conversation" in prompt
    assert "do not treat this alone as grounds for end_conversation" in prompt


def test_build_system_prompt_requires_pending_close_before_end_conversation() -> None:
    prompt = v1.build_system_prompt(v1.PromptContext(agent_name="Support Bot v2"))

    assert "There is no shortcut" in prompt
    assert "okay then thanks" in prompt
    assert "NOT asked 'anything else?' yet" in prompt
    assert "your immediately previous assistant message was pending_close" in prompt


def test_build_system_prompt_includes_known_session_facts() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            session_facts={"user_id": "usr_1", "intent": "refund"},
        )
    )

    assert "Known session facts" in prompt
    assert "user_id: usr_1" in prompt
    assert "session_facts must always be present" in prompt


def test_build_system_prompt_includes_grounding_policy() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            tool_names=("get_user",),
            knowledge_base_context="Refunds within 30 days.",
        )
    )

    assert "Grounding policy (non-negotiable):" in prompt
    assert "Never hallucinate" in prompt
    assert "call an available tool" in prompt

    without_tools = v1.build_system_prompt(v1.PromptContext(agent_name="Support Bot v2"))
    assert "No API tools are available this turn" in without_tools
    assert "No knowledge base context was retrieved" in without_tools


def test_build_system_prompt_includes_capability_disclosure_policy() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            tool_names=("get_transaction_details", "authenticate_user"),
        )
    )

    assert "Capability disclosure (customer-facing replies only):" in prompt
    assert "never expose internal tool names" in prompt
    assert "get_transaction_details" in prompt  # listed for model use in Tools section
    assert "I can help with account questions" in prompt


def test_build_system_prompt_enforces_tool_argument_discipline() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            tool_names=("authenticate_user",),
        )
    )

    assert "Tool argument discipline (strict):" in prompt
    assert "parameter names defined on the tool" in prompt
    assert "conversation_state=waiting_on_customer" in prompt
    assert "Never call tools with empty {} arguments" in prompt


def test_build_system_prompt_includes_escalation_policy() -> None:
    with_tools = v1.build_system_prompt(
        v1.PromptContext(
            agent_name="Support Bot v2",
            tool_names=("lookup_record",),
        )
    )
    without_tools = v1.build_system_prompt(v1.PromptContext(agent_name="Support Bot v2"))

    assert "Escalation (do not give up easily):" in with_tools
    assert "retry ONCE with valid arguments" in with_tools
    assert "internal or system-only parameters" in with_tools
    assert "Resolution before transfer (strict):" in with_tools
    assert "transfer immediately" in with_tools

    assert "Escalation (do not give up easily):" in without_tools
    assert "retry ONCE with valid arguments" not in without_tools


def test_build_system_prompt_omits_ticket_signal_by_default() -> None:
    prompt = v1.build_system_prompt(v1.PromptContext(agent_name="Support Bot v2"))

    assert "Ticket signal" not in prompt
    assert "ticket_action" not in prompt
    assert "issue_resolved" not in prompt


def test_build_system_prompt_includes_ticket_signal_when_enabled() -> None:
    prompt = v1.build_system_prompt(
        v1.PromptContext(agent_name="Support Bot v2", enable_ticket_signal=True)
    )

    assert "Ticket signal (set ticket_action in your JSON reply):" in prompt
    assert "create_ticket" in prompt
    assert "ticket_reason" in prompt
    assert "Issue resolved signal (set issue_resolved in your JSON reply):" in prompt
    assert "issue_resolved" in prompt
    # The required-shape block now advertises the ticket fields to the model.
    assert '"ticket_action": "none"' in prompt
