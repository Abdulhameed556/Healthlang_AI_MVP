"""OpenAI single-task agent provider (langchain-openai)."""
from collections.abc import AsyncIterator
from typing import Any

from langchain_openai import ChatOpenAI

from ai.src.domain.llm.types import (
    SingleTaskAgentRequest,
    SingleTaskAgentResult,
    VisionAgentRequest,
)
from ai.src.infrastructure.llm.providers.base import BaseSingleTaskAgentProvider
from ai.src.infrastructure.llm.providers.langchain_helpers import (
    build_langchain_messages,
    build_vision_langchain_messages,
    message_content_to_str,
    usage_from_message,
)


class OpenAISingleTaskAgentProvider(BaseSingleTaskAgentProvider):
    @property
    def name(self) -> str:
        return "openai"

    def __init__(self, *, api_key: str) -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai provider")
        self._api_key = api_key

    def _build_model(self, request: SingleTaskAgentRequest) -> ChatOpenAI:
        return self._build_chat_model(
            model=request.model,
            max_retries=request.max_retries,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream_usage=request.stream_usage,
        )

    def _build_chat_model(
        self,
        *,
        model: str,
        max_retries: int,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stream_usage: bool = False,
    ) -> ChatOpenAI:
        kwargs: dict[str, Any] = {
            "model": model,
            "api_key": self._api_key,
            "max_retries": max_retries,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if stream_usage:
            kwargs["stream_usage"] = True
        return ChatOpenAI(**kwargs)

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

    async def run_vision(self, request: VisionAgentRequest) -> SingleTaskAgentResult:
        llm = self._build_chat_model(
            model=request.model,
            max_retries=request.max_retries,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        message = await llm.ainvoke(build_vision_langchain_messages(request))
        return SingleTaskAgentResult(
            content=message_content_to_str(message.content),
            provider=self.name,
            model=request.model,
            usage=usage_from_message(message),
        )
