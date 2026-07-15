"""Conversation generator agent — synthetic multi-turn conversations."""
from __future__ import annotations

from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.infrastructure.chat_system.v1.agents.conversation_generator.config import (  # noqa: E501
    AGENT_NAME,
    DEFAULT_CONFIG,
)
from ai.src.infrastructure.chat_system.v1.base.agent import BaseChatSystemAgent


class ConversationGeneratorAgent(BaseChatSystemAgent):
    """Generates synthetic customer↔agent conversations for eval."""

    def __init__(
        self,
        config: AgentLLMConfig | None = None,
        runner=None,
    ) -> None:
        super().__init__(config or DEFAULT_CONFIG, runner=runner)

    @property
    def name(self) -> str:
        return AGENT_NAME

    async def generate(
        self,
        scenario_name: str,
        scenario_description: str,
        scenario_prompt: str,
        persona_1: str,
        persona_2: str,
        knowledge_bases: list[dict],
        rules: list[str],
        agent_name: str = "Support Agent",
        conversation_rounds: int = 5,
        agent_variables: dict | None = None,
    ) -> list[dict]:
        """Return [{persona, turns:[{user,agent_expected}]}]."""
        prompts = self._load_prompts()
        ctx = prompts.PromptContext(
            agent_name=agent_name,
            scenario_name=scenario_name,
            scenario_description=scenario_description,
            scenario_prompt=scenario_prompt,
            persona_1=persona_1,
            persona_2=persona_2,
            knowledge_bases=knowledge_bases,
            rules=list(rules),
            conversation_rounds=conversation_rounds,
            agent_variables=agent_variables or {},
        )
        result = await self._run_structured_with_fallback(
            system_prompt=prompts.build_system_prompt(ctx),
            user_prompt=prompts.build_user_prompt(ctx),
            output_format=prompts.OUTPUT_FORMAT,
        )
        if not result.parse_success or not result.data:
            return []
        raw = result.data.get("conversations", [])
        return [c for c in raw if isinstance(c, dict) and c.get("turns")]
