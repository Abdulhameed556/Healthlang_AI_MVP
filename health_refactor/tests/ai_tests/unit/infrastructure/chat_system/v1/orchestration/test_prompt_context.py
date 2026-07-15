"""Unit tests: orchestration prompt context builder."""
from uuid import uuid4

from backend.src.domain.agents.brand_personalization import (
    brand_config_from_dict,
    personalization_config_from_dict,
)
from backend.src.infrastructure.agent_runtime.types import AgentRuntimeContext
from ai.src.infrastructure.chat_system.v1.orchestration.prompt_context import build_prompt_context


def test_build_prompt_context_maps_runtime_brand_and_personalization() -> None:
    runtime = AgentRuntimeContext(
        agent_id=uuid4(),
        organization_id=uuid4(),
        version_id=uuid4(),
        version_number=1,
        agent_name="Support Bot",
        brand_config=brand_config_from_dict({"company_name": "Acme", "languages": ["english"]}),
        personalization_config=personalization_config_from_dict(
            {"tone_profile": "friendly_casual", "formality": "casual", "pacing": 1.2}
        ),
        scenarios=(),
        rules=(),
        knowledge_bases=(),
    )

    ctx = build_prompt_context(
        runtime,
        scenario_prompt="Handle billing questions.",
        rules=("Privacy: Never ask for passwords.",),
        knowledge_base_context="Billing FAQ chunk.",
        tool_names=("get_company_doc",),
        session_conversation_state="in_progress",
    )

    assert ctx.agent_name == "Support Bot"
    assert ctx.brand_config.company_name == "Acme"
    assert ctx.personalization_config.tone_profile == "friendly_casual"
    assert ctx.scenario_prompt == "Handle billing questions."
    assert ctx.rules == ("Privacy: Never ask for passwords.",)
    assert ctx.knowledge_base_context == "Billing FAQ chunk."
