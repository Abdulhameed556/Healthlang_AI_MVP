"""Anthropic single-task agent provider (langchain-anthropic)."""
from collections.abc import AsyncIterator
from typing import Any

from langchain_anthropic import ChatAnthropic

from ai.src.domain.llm.types import SingleTaskAgentRequest, SingleTaskAgentResult
from ai.src.infrastructure.llm.providers.base import BaseSingleTaskAgentProvider
from ai.src.infrastructure.llm.providers.langchain_helpers import (
    build_langchain_messages,
    message_content_to_str,
    usage_from_message,
)


class AnthropicSingleTaskAgentProvider(BaseSingleTaskAgentProvider):
    @property
    def name(self) -> str:
        return "anthropic"

    def __init__(self, *, api_key: str) -> None:
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for the anthropic provider")
        self._api_key = api_key

    def _build_model(self, request: SingleTaskAgentRequest) -> ChatAnthropic:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "api_key": self._api_key,
            "max_retries": request.max_retries,
        }
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        return ChatAnthropic(**kwargs)

    async def run(self, request: SingleTaskAgentRequest) -> SingleTaskAgentResult:
        if request.stream:
            chunks: list[str] = []
            async for chunk in self.stream(request):
                chunks.append(chunk)
            return SingleTaskAgentResult(
                content="".join(chunks),
                provider=self.name,
                model=request.model,
                usage=None,
            )

        llm = self._build_model(request)
        message = await llm.ainvoke(build_langchain_messages(request))
        return SingleTaskAgentResult(
            content=message_content_to_str(message.content),
            provider=self.name,
            model=request.model,
            usage=usage_from_message(message),
        )

    async def stream(self, request: SingleTaskAgentRequest) -> AsyncIterator[str]:
        llm = self._build_model(request)
        async for chunk in llm.astream(build_langchain_messages(request)):
            text = message_content_to_str(chunk.content) if chunk.content else ""
            if text:
                yield text
