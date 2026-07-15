"""Unit tests: judge criteria agent handler."""
from unittest.mock import AsyncMock, MagicMock

import pytest

from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.domain.llm.types import StructuredSingleTaskAgentResult
from ai.src.infrastructure.chat_system.v1.agents.judge_criteria.handler import (  # noqa: E501
    JudgeCriteriaAgent,
)


def _runner_with(data: dict, parse_success: bool = True) -> MagicMock:
    runner = MagicMock()
    runner.run_structured = AsyncMock(
        return_value=StructuredSingleTaskAgentResult(
            data=data,
            raw=str(data),
            provider="openai",
            model="gpt-4o-mini",
            parse_success=parse_success,
        )
    )
    return runner


def _agent(runner=None) -> JudgeCriteriaAgent:
    return JudgeCriteriaAgent(
        config=AgentLLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            prompt_version="v1",
        ),
        runner=runner or _runner_with({"scores": []}),
    )


TRANSCRIPT = "Turn 1\n  Customer: Where is my money?\n  Agent: I'll check."


# ── score(): happy path ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_score_returns_dict_keyed_by_criterion() -> None:
    runner = _runner_with({
        "scores": [
            {
                "criterion": "Agent acknowledged the issue.",
                "score": 0.9,
                "reason": "Agent said I'll check immediately.",
            }
        ]
    })
    result = await _agent(runner).score(
        transcript=TRANSCRIPT,
        criteria=["Agent acknowledged the issue."],
    )

    assert "Agent acknowledged the issue." in result
    entry = result["Agent acknowledged the issue."]
    assert entry["score"] == pytest.approx(0.9)
    assert entry["reason"] == "Agent said I'll check immediately."


@pytest.mark.asyncio
async def test_score_clamps_values_to_0_1() -> None:
    runner = _runner_with({
        "scores": [
            {"criterion": "A", "score": 1.5, "reason": "over"},
            {"criterion": "B", "score": -0.2, "reason": "under"},
        ]
    })
    result = await _agent(runner).score(
        transcript=TRANSCRIPT, criteria=["A", "B"]
    )

    assert result["A"]["score"] == pytest.approx(1.0)
    assert result["B"]["score"] == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_score_handles_multiple_criteria() -> None:
    runner = _runner_with({
        "scores": [
            {"criterion": "Tone", "score": 0.8, "reason": "polite"},
            {"criterion": "Accuracy", "score": 0.6, "reason": "mostly"},
        ]
    })
    result = await _agent(runner).score(
        transcript=TRANSCRIPT, criteria=["Tone", "Accuracy"]
    )

    assert len(result) == 2
    assert result["Tone"]["score"] == pytest.approx(0.8)
    assert result["Tone"]["reason"] == "polite"
    assert result["Accuracy"]["score"] == pytest.approx(0.6)


# ── score(): early returns ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_score_empty_criteria_returns_empty_dict() -> None:
    runner = _runner_with({"scores": []})
    result = await _agent(runner).score(
        transcript=TRANSCRIPT, criteria=[]
    )

    assert result == {}
    runner.run_structured.assert_not_called()


@pytest.mark.asyncio
async def test_score_parse_failure_returns_empty_dict() -> None:
    runner = _runner_with({}, parse_success=False)
    result = await _agent(runner).score(
        transcript=TRANSCRIPT, criteria=["A criterion"]
    )

    assert result == {}


@pytest.mark.asyncio
async def test_score_missing_scores_key_returns_empty_dict() -> None:
    runner = _runner_with({"unexpected": "shape"})
    result = await _agent(runner).score(
        transcript=TRANSCRIPT, criteria=["A criterion"]
    )

    assert result == {}


@pytest.mark.asyncio
async def test_score_skips_entries_with_non_numeric_score() -> None:
    runner = _runner_with({
        "scores": [
            {"criterion": "Valid", "score": 0.7, "reason": "ok"},
            {"criterion": "Invalid", "score": "high", "reason": "bad"},
        ]
    })
    result = await _agent(runner).score(
        transcript=TRANSCRIPT, criteria=["Valid", "Invalid"]
    )

    assert "Valid" in result
    assert result["Valid"]["score"] == pytest.approx(0.7)
    assert "Invalid" not in result


def test_agent_name() -> None:
    assert _agent().name == "judge_criteria"


@pytest.mark.asyncio
async def test_score_skips_non_dict_entries_in_scores() -> None:
    runner = _runner_with({
        "scores": [
            "not a dict",
            {"criterion": "Valid", "score": 0.8, "reason": "ok"},
        ]
    })
    result = await _agent(runner).score(
        transcript=TRANSCRIPT, criteria=["Valid"]
    )

    assert "Valid" in result
    assert len(result) == 1
