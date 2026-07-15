"""Guardrail input screener — blocks prompt injection and policy violations."""
from __future__ import annotations

from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    GuardrailInputScreenerInput,
    GuardrailInputScreenerResult,
    PromptInjectionCategory,
)
from ai.src.infrastructure.chat_system.v1.agents.guardrail_input_screener.config import (
    AGENT_NAME,
    DEFAULT_CONFIG,
)
from ai.src.infrastructure.chat_system.v1.base.agent import BaseChatSystemAgent
from ai.src.infrastructure.chat_system.v1.base.guardrail import map_structured_guardrail


class GuardrailInputScreenerAgent(BaseChatSystemAgent):
    """Screens user input for prompt injection and custom rule violations."""

    def __init__(
        self,
        config: AgentLLMConfig | None = None,
        runner=None,
    ) -> None:
        super().__init__(config or DEFAULT_CONFIG, runner=runner)

    @property
    def name(self) -> str:
        return AGENT_NAME

    async def run(self, input: GuardrailInputScreenerInput) -> GuardrailInputScreenerResult:
        prompts = self._load_prompts()
        ctx = prompts.PromptContext(
            user_query=input.user_query,
            message_history=input.message_history,
            rules=input.rules,
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

        decision = map_structured_guardrail(
            result,
            PromptInjectionCategory,
            category_key="attack_category",
            none_category=PromptInjectionCategory.NONE,
            custom_rule_category=PromptInjectionCategory.CUSTOM_RULE,
            parse_failure_reason="Unable to validate user input.",
            default_block_reason="Input blocked by guardrail policy.",
        )
        return GuardrailInputScreenerResult(
            blocked=decision.blocked,
            blocked_reason=decision.blocked_reason,
            attack_category=decision.category,  # type: ignore[arg-type]
            raw=result.raw,
            provider=result.provider,
            model=result.model,
            parse_success=decision.parse_success,
        )
