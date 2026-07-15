"""Base single-task provider with shared structured-output support."""
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from ai.src.domain.llm.structured import run_structured_completion
from ai.src.domain.llm.types import (
    SingleTaskAgentRequest,
    SingleTaskAgentResult,
    StructuredSingleTaskAgentRequest,
    StructuredSingleTaskAgentResult,
)


class BaseSingleTaskAgentProvider(ABC):
    """Implement ``run`` and ``stream``; ``run_structured`` is provided by default."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def run(self, request: SingleTaskAgentRequest) -> SingleTaskAgentResult: ...

    @abstractmethod
    async def stream(self, request: SingleTaskAgentRequest) -> AsyncIterator[str]: ...

    async def run_structured(
        self,
        request: StructuredSingleTaskAgentRequest,
    ) -> StructuredSingleTaskAgentResult:
        return await run_structured_completion(self.run, request)
