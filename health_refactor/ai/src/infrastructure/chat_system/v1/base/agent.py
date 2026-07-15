"""Shared LLM execution for chat-system agents."""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from types import ModuleType

from ai.src.application.single_task_agent.runner import SingleTaskAgentRunner
from ai.src.core.exceptions import LLMError
from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.messages import ChatMessage
from ai.src.domain.llm.types import (
    SingleTaskAgentRequest,
    SingleTaskAgentResult,
    StructuredSingleTaskAgentRequest,
    StructuredSingleTaskAgentResult,
)
from ai.src.infrastructure.chat_system.v1.base.prompts import load_prompt_module
from ai.src.infrastructure.chat_system.v1.llm_logging import (
    log_llm_call,
    result_output_preview,
)


class BaseChatSystemAgent(ABC):
    def __init__(
        self,
        config: AgentLLMConfig,
        runner: SingleTaskAgentRunner | None = None,
    ) -> None:
        self._config = config
        self._runner = runner or SingleTaskAgentRunner()

    @property
    @abstractmethod
    def name(self) -> str: ...

    def _load_prompts(self) -> ModuleType:
        return load_prompt_module(self.name, self._config.prompt_version)

    async def _run_text_with_fallback(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        message_history: tuple[ChatMessage, ...] = (),
    ) -> SingleTaskAgentResult:
        async def attempt(provider: str, model: str) -> SingleTaskAgentResult:
            return await self._runner.run(
                SingleTaskAgentRequest(
                    system_prompt=system_prompt,
                    prompt=user_prompt,
                    provider=provider,
                    model=model,
                    message_history=message_history,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                    max_retries=self._config.max_retries,
                )
            )

        return await self._execute_with_fallback(attempt)

    async def _run_structured_with_fallback(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        output_format: JsonOutputFormat,
        message_history: tuple[ChatMessage, ...] = (),
    ) -> StructuredSingleTaskAgentResult:
        async def attempt(provider: str, model: str) -> StructuredSingleTaskAgentResult:
            return await self._runner.run_structured(
                StructuredSingleTaskAgentRequest(
                    system_prompt=system_prompt,
                    prompt=user_prompt,
                    provider=provider,
                    model=model,
                    output_format=output_format,
                    message_history=message_history,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                    max_retries=self._config.max_retries,
                )
            )

        return await self._execute_with_fallback(attempt)

    async def _execute_with_fallback(
        self,
        attempt: Callable[[str, str], Awaitable[SingleTaskAgentResult | StructuredSingleTaskAgentResult]],
    ) -> SingleTaskAgentResult | StructuredSingleTaskAgentResult:
        started = time.perf_counter()
        try:
            result = await attempt(self._config.provider, self._config.model)
        except Exception as primary_error:
            duration_ms = (time.perf_counter() - started) * 1000
            log_llm_call(
                component=self.name,
                attempt="primary",
                provider=self._config.provider,
                model=self._config.model,
                outcome="failed",
                duration_ms=duration_ms,
                error=str(primary_error),
            )
            if not self._config.fallback_provider:
                raise LLMError(
                    f"{self.name} primary provider failed: {primary_error}"
                ) from primary_error

            fallback_model = self._config.fallback_model or self._config.model
            fallback_started = time.perf_counter()
            try:
                result = await attempt(
                    self._config.fallback_provider,
                    fallback_model,
                )
            except Exception as fallback_error:
                fallback_duration_ms = (time.perf_counter() - fallback_started) * 1000
                log_llm_call(
                    component=self.name,
                    attempt="fallback",
                    provider=self._config.fallback_provider,
                    model=fallback_model,
                    outcome="failed",
                    duration_ms=fallback_duration_ms,
                    error=str(fallback_error),
                )
                raise LLMError(
                    f"{self.name} primary and fallback providers failed"
                ) from fallback_error

            fallback_duration_ms = (time.perf_counter() - fallback_started) * 1000
            parse_success = getattr(result, "parse_success", None)
            log_llm_call(
                component=self.name,
                attempt="fallback",
                provider=result.provider,
                model=result.model,
                outcome="ok",
                duration_ms=fallback_duration_ms,
                usage=result.usage,
                output_preview=result_output_preview(result),
                parse_success=parse_success,
            )
            return result

        duration_ms = (time.perf_counter() - started) * 1000
        parse_success = getattr(result, "parse_success", None)
        log_llm_call(
            component=self.name,
            attempt="primary",
            provider=result.provider,
            model=result.model,
            outcome="ok",
            duration_ms=duration_ms,
            usage=result.usage,
            output_preview=result_output_preview(result),
            parse_success=parse_success,
        )
        return result
