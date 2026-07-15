"""LLM client interfaces — application layer depends on these only."""
from typing import AsyncIterator, Protocol

from ai.src.domain.llm.types import (
    SingleTaskAgentRequest,
    SingleTaskAgentResult,
    StructuredSingleTaskAgentRequest,
    StructuredSingleTaskAgentResult,
)


class ILLMClient(Protocol):
    async def complete(self, messages: list[dict], **kwargs) -> str: ...
    async def stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]: ...
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class ISingleTaskAgentProvider(Protocol):
    """Provider plugin for a one-shot system + user prompt completion."""

    @property
    def name(self) -> str: ...

    async def run(self, request: SingleTaskAgentRequest) -> SingleTaskAgentResult: ...

    async def stream(self, request: SingleTaskAgentRequest) -> AsyncIterator[str]: ...

    async def run_structured(
        self, request: StructuredSingleTaskAgentRequest
    ) -> StructuredSingleTaskAgentResult: ...
