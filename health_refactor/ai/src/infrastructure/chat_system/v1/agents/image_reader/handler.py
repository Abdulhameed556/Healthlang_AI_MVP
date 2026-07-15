"""Image reader — extracts text and context from customer image attachments."""
from __future__ import annotations

import time

from ai.src.application.single_task_agent.runner import SingleTaskAgentRunner
from ai.src.core.exceptions import LLMError
from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    ImageReaderAgentInput,
    ImageReaderAgentResult,
)
from ai.src.domain.llm.types import VisionAgentRequest
from ai.src.infrastructure.chat_system.v1.agents.image_reader.config import (
    AGENT_NAME,
    DEFAULT_CONFIG,
)
from ai.src.infrastructure.chat_system.v1.base.prompts import load_prompt_module
from ai.src.infrastructure.chat_system.v1.llm_logging import (
    log_llm_call,
    result_output_preview,
)


class ImageReaderAgent:
    """Vision preprocessing agent for inbound image attachments."""

    def __init__(
        self,
        config: AgentLLMConfig | None = None,
        runner: SingleTaskAgentRunner | None = None,
    ) -> None:
        self._config = config or DEFAULT_CONFIG
        self._runner = runner or SingleTaskAgentRunner()

    @property
    def name(self) -> str:
        return AGENT_NAME

    async def run(self, input: ImageReaderAgentInput) -> ImageReaderAgentResult:
        if not input.image_urls:
            return ImageReaderAgentResult(
                description="",
                raw="",
                provider=self._config.provider,
                model=self._config.model,
                success=False,
                error="no_image_urls",
            )

        prompts = load_prompt_module(self.name, self._config.prompt_version)
        ctx = prompts.PromptContext(caption=input.caption)
        system_prompt = prompts.build_system_prompt(ctx)
        user_prompt = prompts.build_user_prompt(ctx)

        try:
            result = await self._run_vision_with_fallback(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                image_urls=input.image_urls,
            )
        except LLMError as exc:
            return ImageReaderAgentResult(
                description="",
                raw="",
                provider=self._config.provider,
                model=self._config.model,
                success=False,
                error=str(exc),
            )

        description = (result.content or "").strip()
        return ImageReaderAgentResult(
            description=description,
            raw=result.content,
            provider=result.provider,
            model=result.model,
            success=bool(description),
            error=None if description else "empty_description",
        )

    async def _run_vision_with_fallback(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_urls: tuple[str, ...],
    ):
        async def attempt(provider: str, model: str):
            return await self._runner.run_vision(
                VisionAgentRequest(
                    system_prompt=system_prompt,
                    prompt=user_prompt,
                    image_urls=image_urls,
                    provider=provider,
                    model=model,
                    temperature=self._config.temperature,
                    max_tokens=self._config.max_tokens,
                    max_retries=self._config.max_retries,
                )
            )

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
                result = await attempt(self._config.fallback_provider, fallback_model)
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
            log_llm_call(
                component=self.name,
                attempt="fallback",
                provider=result.provider,
                model=result.model,
                outcome="ok",
                duration_ms=fallback_duration_ms,
                usage=result.usage,
                output_preview=result_output_preview(result),
            )
            return result

        duration_ms = (time.perf_counter() - started) * 1000
        log_llm_call(
            component=self.name,
            attempt="primary",
            provider=result.provider,
            model=result.model,
            outcome="ok",
            duration_ms=duration_ms,
            usage=result.usage,
            output_preview=result_output_preview(result),
        )
        return result
