"""Shared structured-output orchestration for single-task providers."""
from collections.abc import Awaitable, Callable

from ai.src.domain.llm.json_parser import parse_json_output
from ai.src.domain.llm.structured_prompt import build_structured_system_prompt
from ai.src.domain.llm.types import (
    SingleTaskAgentRequest,
    SingleTaskAgentResult,
    StructuredSingleTaskAgentRequest,
    StructuredSingleTaskAgentResult,
)


async def run_structured_completion(
    complete: Callable[[SingleTaskAgentRequest], Awaitable[SingleTaskAgentResult]],
    request: StructuredSingleTaskAgentRequest,
) -> StructuredSingleTaskAgentResult:
    """Run a completion with JSON shape in the system prompt, then parse <json> output."""
    llm_request = SingleTaskAgentRequest(
        system_prompt=build_structured_system_prompt(
            request.system_prompt,
            request.output_format,
        ),
        prompt=request.prompt,
        provider=request.provider,
        model=request.model,
        message_history=request.message_history,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        max_retries=request.max_retries,
        stream=False,
        stream_usage=request.stream_usage,
    )
    result = await complete(llm_request)
    parsed = parse_json_output(result.content, request.output_format)
    return StructuredSingleTaskAgentResult(
        data=parsed.data,
        raw=result.content,
        provider=result.provider,
        model=result.model,
        usage=result.usage,
        parse_success=parsed.success,
        parse_errors=tuple(parsed.errors),
    )
