"""Unit tests: ai/src/infrastructure/llm/providers/base.py"""
import pytest

from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.domain.llm.types import (
    SingleTaskAgentRequest,
    SingleTaskAgentResult,
    StructuredSingleTaskAgentRequest,
)
from ai.src.infrastructure.llm.providers.base import BaseSingleTaskAgentProvider


class _StubProvider(BaseSingleTaskAgentProvider):
    @property
    def name(self) -> str:
        return "stub"

    async def run(self, request: SingleTaskAgentRequest) -> SingleTaskAgentResult:
        return SingleTaskAgentResult(
            content='<json>{"name": "Acme"}</json>',
            provider=self.name,
            model=request.model,
        )

    async def stream(self, request: SingleTaskAgentRequest):
        yield "x"


@pytest.mark.asyncio
async def test_run_structured_parses_json() -> None:
    fmt = JsonOutputFormat.from_example({"name": "sam"})
    request = StructuredSingleTaskAgentRequest(
        system_prompt="Extract name.",
        prompt="Name is Acme",
        provider="stub",
        model="gpt-4o-mini",
        output_format=fmt,
    )

    result = await _StubProvider().run_structured(request)

    assert result.parse_success is True
    assert result.data == {"name": "Acme"}
    assert "Acme" in result.raw


@pytest.mark.asyncio
async def test_run_structured_injects_template_into_system_prompt() -> None:
    captured: list[SingleTaskAgentRequest] = []

    class _CapturingProvider(BaseSingleTaskAgentProvider):
        @property
        def name(self) -> str:
            return "cap"

        async def run(self, request: SingleTaskAgentRequest) -> SingleTaskAgentResult:
            captured.append(request)
            return SingleTaskAgentResult(
                content='<json>{"name": "x"}</json>',
                provider=self.name,
                model=request.model,
            )

        async def stream(self, request: SingleTaskAgentRequest):
            yield ""

    fmt = JsonOutputFormat.from_example({"name": "sam"})
    await _CapturingProvider().run_structured(
        StructuredSingleTaskAgentRequest(
            system_prompt="Base task.",
            prompt="go",
            provider="cap",
            model="m",
            output_format=fmt,
        )
    )

    assert len(captured) == 1
    assert "Base task." in captured[0].system_prompt
    assert '"name": "sam"' in captured[0].system_prompt
    assert "Required shape:" in captured[0].system_prompt
    assert "Output format (MANDATORY)" in captured[0].system_prompt


@pytest.mark.asyncio
async def test_run_structured_forwards_message_history() -> None:
    captured: list[SingleTaskAgentRequest] = []

    class _CapturingProvider(BaseSingleTaskAgentProvider):
        @property
        def name(self) -> str:
            return "cap"

        async def run(self, request: SingleTaskAgentRequest) -> SingleTaskAgentResult:
            captured.append(request)
            return SingleTaskAgentResult(
                content='<json>{"name": "x"}</json>',
                provider=self.name,
                model=request.model,
            )

        async def stream(self, request: SingleTaskAgentRequest):
            yield ""

    history = (ChatMessage(role=MessageRole.USER, content="prior"),)
    fmt = JsonOutputFormat.from_example({"name": "sam"})
    await _CapturingProvider().run_structured(
        StructuredSingleTaskAgentRequest(
            system_prompt="Base.",
            prompt="go",
            provider="cap",
            model="m",
            output_format=fmt,
            message_history=history,
        )
    )

    assert captured[0].message_history == history
