"""Build orchestration PromptContext from deployed agent runtime."""
from __future__ import annotations

from backend.src.infrastructure.agent_runtime.types import AgentRuntimeContext
from ai.src.infrastructure.chat_system.v1.orchestration.prompts import load_prompt_module


def build_prompt_context(
    runtime: AgentRuntimeContext,
    *,
    scenario_prompt: str | None = None,
    rules: tuple[str, ...] = (),
    knowledge_base_context: str | None = None,
    tool_names: tuple[str, ...] = (),
    session_conversation_state: str | None = None,
    session_facts: dict[str, str] | None = None,
    enable_ticket_signal: bool = False,
    prompt_version: str | None = None,
):
    """Map deployed runtime + turn inputs to the versioned orchestration prompt context."""
    prompts = load_prompt_module(prompt_version)
    return prompts.PromptContext(
        agent_name=runtime.agent_name,
        brand_config=runtime.brand_config,
        personalization_config=runtime.personalization_config,
        scenario_prompt=scenario_prompt,
        rules=rules,
        knowledge_base_context=knowledge_base_context,
        tool_names=tool_names,
        session_conversation_state=session_conversation_state,
        session_facts=session_facts,
        enable_ticket_signal=enable_ticket_signal,
    )
