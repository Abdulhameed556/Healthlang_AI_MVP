"""Pipeline step: score completed conversations against judge criteria."""
from __future__ import annotations

import asyncio

from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.domain.chat_evaluation.entities import ConversationCaseResult
from ai.src.infrastructure.chat_system.v1.agents.judge_criteria import (
    JudgeCriteriaAgent,
)


def _format_transcript(result: ConversationCaseResult) -> str:
    parts: list[str] = []
    for i, turn in enumerate(result.turns, 1):
        parts.append(f"Turn {i}")
        parts.append(f"  Customer: {turn.user}")
        parts.append(f"  Agent: {turn.agent_actual}")
    return "\n".join(parts)


class ScoreWithJudgeStep:
    """Score each ConversationCaseResult against ctx.judge_criteria."""

    def __init__(self, agent: JudgeCriteriaAgent | None = None) -> None:
        self._agent = agent or JudgeCriteriaAgent()

    async def run(self, ctx: ChatEvalContext) -> None:
        if not ctx.judge_criteria:
            return

        scorable = [
            r for r in ctx.results
            if isinstance(r, ConversationCaseResult) and r.turns
        ]

        async def _score_one(result: ConversationCaseResult) -> None:
            try:
                result.judge_scores = await self._agent.score(
                    transcript=_format_transcript(result),
                    criteria=ctx.judge_criteria,
                )
            except Exception:  # noqa: BLE001
                pass

        await asyncio.gather(*[_score_one(r) for r in scorable])
