"""Run a single-task agent call via a registered LLM provider."""
from collections.abc import AsyncIterator

from ai.src.domain.llm.types import (
    SingleTaskAgentRequest,
    SingleTaskAgentResult,
    StructuredSingleTaskAgentRequest,
    StructuredSingleTaskAgentResult,
    VisionAgentRequest,
)
from ai.src.infrastructure.llm.factory import get_single_task_provider


class SingleTaskAgentRunner:
    async def run(self, request: SingleTaskAgentRequest) -> SingleTaskAgentResult:
        provider = get_single_task_provider(request.provider)
        return await provider.run(request)

    async def stream(self, request: SingleTaskAgentRequest) -> AsyncIterator[str]:
        provider = get_single_task_provider(request.provider)
        async for chunk in provider.stream(request):
            yield chunk

    async def run_structured(
        self, request: StructuredSingleTaskAgentRequest
    ) -> StructuredSingleTaskAgentResult:
        provider = get_single_task_provider(request.provider)
        return await provider.run_structured(request)

    async def run_vision(self, request: VisionAgentRequest) -> SingleTaskAgentResult:
        provider = get_single_task_provider(request.provider)
        run_vision = getattr(provider, "run_vision", None)
        if run_vision is None:
            raise ValueError(f"Provider {request.provider!r} does not support vision")
        return await run_vision(request)
