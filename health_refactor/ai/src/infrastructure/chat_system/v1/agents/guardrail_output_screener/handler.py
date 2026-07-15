"""Guardrail output screener — pass, reformat, or block assistant responses."""
from __future__ import annotations

from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    GuardrailOutputScreenerInput,
    GuardrailOutputScreenerResult,
)
from ai.src.infrastructure.chat_system.v1.agents.guardrail_output_screener.config import (
    AGENT_NAME,
    DEFAULT_CONFIG,
)
from ai.src.infrastructure.chat_system.v1.agents.guardrail_output_screener.mapper import (
    map_output_screening,
)
from ai.src.infrastructure.chat_system.v1.base.agent import BaseChatSystemAgent


class GuardrailOutputScreenerAgent(BaseChatSystemAgent):
    """Screens assistant output before it reaches the user."""

    def __init__(
        self,
        config: AgentLLMConfig | None = None,
        runner=None,
    ) -> None:
        super().__init__(config or DEFAULT_CONFIG, runner=runner)

    @property
    def name(self) -> str:
        return AGENT_NAME

    async def run(self, input: GuardrailOutputScreenerInput) -> GuardrailOutputScreenerResult:
        prompts = self._load_prompts()
        ctx = prompts.PromptContext(
            agent_output=input.agent_output,
            user_query=input.user_query,
            message_history=input.message_history,
            rules=input.rules,
            tools_used=input.tools_used,
            agent_name=input.agent_name,
            brand_config=input.brand_config,
            personalization_config=input.personalization_config,
            sentinel=input.sentinel,
        )
        system_prompt = prompts.build_system_prompt(ctx)
        user_prompt = prompts.build_user_prompt(ctx)

        result = await self._run_structured_with_fallback(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            output_format=prompts.OUTPUT_FORMAT,
            message_history=input.message_history,
        )

        decision = map_output_screening(result)
        return GuardrailOutputScreenerResult(
            action=decision.action,
            blocked=decision.blocked,
            safe_message=decision.safe_message,
            blocked_reason=decision.blocked_reason,
            violation_category=decision.violation_category,
            raw=result.raw,
            provider=result.provider,
            model=result.model,
            parse_success=decision.parse_success,
        )
