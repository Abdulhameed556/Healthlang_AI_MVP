"""Judge criteria agent — scores conversations against custom criteria."""
from __future__ import annotations

from ai.src.domain.chat_system.v1.types import AgentLLMConfig
from ai.src.infrastructure.chat_system.v1.agents.judge_criteria.config import (
    AGENT_NAME,
    DEFAULT_CONFIG,
)
from ai.src.infrastructure.chat_system.v1.base.agent import BaseChatSystemAgent


class JudgeCriteriaAgent(BaseChatSystemAgent):
    """Scores a conversation transcript against a list of criteria (0–1)."""

    def __init__(
        self,
        config: AgentLLMConfig | None = None,
        runner=None,
    ) -> None:
        super().__init__(config or DEFAULT_CONFIG, runner=runner)

    @property
    def name(self) -> str:
        return AGENT_NAME

    async def score(
        self,
        transcript: str,
        criteria: list[str],
    ) -> dict[str, dict]:
        """Return {criterion_text: {score, reason}} for each criterion.

        On parse failure, returns an empty dict so the pipeline continues.
        """
        if not criteria:
            return {}

        prompts = self._load_prompts()
        ctx = prompts.PromptContext(
            transcript=transcript,
            criteria=list(criteria),
        )
        result = await self._run_structured_with_fallback(
            system_prompt=prompts.build_system_prompt(ctx),
            user_prompt=prompts.build_user_prompt(ctx),
            output_format=prompts.OUTPUT_FORMAT,
        )
        if not result.parse_success or not result.data:
            return {}

        scores: dict[str, dict] = {}
        for entry in result.data.get("scores", []):
            if not isinstance(entry, dict):
                continue
            criterion = entry.get("criterion", "")
            raw_score = entry.get("score")
            reason = entry.get("reason", "")
            if criterion and isinstance(raw_score, (int, float)):
                scores[criterion] = {
                    "score": float(max(0.0, min(1.0, raw_score))),
                    "reason": str(reason),
                }
        return scores
