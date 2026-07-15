"""Gemini single-task agent provider (langchain-google-genai)."""
from collections.abc import AsyncIterator
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI

from ai.src.domain.llm.types import SingleTaskAgentRequest, SingleTaskAgentResult
from ai.src.infrastructure.llm.providers.base import BaseSingleTaskAgentProvider
from ai.src.infrastructure.llm.providers.langchain_helpers import (
    build_langchain_messages,
    extract_message_text,
    usage_from_message,
)


class GeminiSingleTaskAgentProvider(BaseSingleTaskAgentProvider):
    @property
    def name(self) -> str:
        return "gemini"

    def __init__(self, *, api_key: str) -> None:
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY is required for the gemini provider"
            )
        self._api_key = api_key

    def _build_model(self, request: SingleTaskAgentRequest) -> ChatGoogleGenerativeAI:
        kwargs: dict[str, Any] = {
            "model": request.model,
            "google_api_key": self._api_key,
            "max_retries": request.max_retries,
        }
        if request.temperature is not None:
            kwargs["temperature"] = request.temperature
        if request.max_tokens is not None:
            kwargs["max_tokens"] = request.max_tokens
        return ChatGoogleGenerativeAI(**kwargs)

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
            content=extract_message_text(message),
            provider=self.name,
            model=request.model,
            usage=usage_from_message(message),
        )

    async def stream(self, request: SingleTaskAgentRequest) -> AsyncIterator[str]:
        llm = self._build_model(request)
        async for chunk in llm.astream(build_langchain_messages(request)):
            text = extract_message_text(chunk) if chunk.content else ""
            if text:
                yield text
