"""Unit tests: image reader agent handler."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.domain.chat_system.v1.types import (
    AgentLLMConfig,
    ImageReaderAgentInput,
)
from ai.src.domain.llm.types import SingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.image_reader.handler import (
    ImageReaderAgent,
)


@pytest.mark.asyncio
async def test_run_returns_description_from_vision() -> None:
    runner = MagicMock()
    runner.run_vision = AsyncMock(
        return_value=SingleTaskAgentResult(
            content="Screenshot shows error: Transaction failed. Amount $50.",
            provider="openai",
            model="gpt-4o",
        )
    )
    agent = ImageReaderAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o",
            prompt_version="v1",
        ),
        runner=runner,
    )

    result = await agent.run(
        ImageReaderAgentInput(
            image_urls=("https://example.com/receipt.jpg",),
            caption="This is my payment",
        )
    )

    assert result.success is True
    assert "Transaction failed" in result.description
    assert result.provider == "openai"
    request = runner.run_vision.await_args.args[0]
    assert request.image_urls == ("https://example.com/receipt.jpg",)
    assert "This is my payment" in request.prompt


@pytest.mark.asyncio
async def test_run_rejects_missing_image_urls() -> None:
    agent = ImageReaderAgent()

    result = await agent.run(ImageReaderAgentInput(image_urls=()))

    assert result.success is False
    assert result.error == "no_image_urls"


@pytest.mark.asyncio
async def test_run_marks_empty_model_output_as_failure() -> None:
    runner = MagicMock()
    runner.run_vision = AsyncMock(
        return_value=SingleTaskAgentResult(
            content="   ",
            provider="openai",
            model="gpt-4o",
        )
    )
    agent = ImageReaderAgent(
        config=AgentLLMConfig(provider="openai", model="gpt-4o", prompt_version="v1"),
        runner=runner,
    )

    result = await agent.run(
        ImageReaderAgentInput(image_urls=("https://example.com/img.jpg",))
    )

    assert result.success is False
    assert result.error == "empty_description"


@pytest.mark.asyncio
async def test_run_uses_default_config_and_agent_name() -> None:
    agent = ImageReaderAgent()

    assert agent.name == "image_reader"
