"""Pipeline step: auto-label expected scenarios for unlabelled test cases."""
from __future__ import annotations

from uuid import UUID

from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.infrastructure.chat_evaluation.scenario_labeler import ScenarioLabelJudge
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    load_scenario_runtime,
)


class LabelExpectedScenariosStep:
    """Loads the agent's scenario catalog and auto-labels any test case whose
    expected_scenario_ids is empty using an independent LLM judge."""

    def __init__(self, judge: ScenarioLabelJudge | None = None) -> None:
        self._judge = judge or ScenarioLabelJudge()

    async def run(self, ctx: ChatEvalContext) -> None:
        if not ctx.agent_id:
            raise ValueError("agent_id is required for scenario evaluation")

        runtime = await load_scenario_runtime(UUID(ctx.agent_id))
        catalog: list[tuple[str, str, str]] = [
            (str(s.id), s.name, s.description or "")
            for s in runtime.scenarios
        ]
        ctx.scenarios_catalog = catalog

        for tc in ctx.test_cases:
            if not tc.get("expected_scenario_ids"):
                ids, reason = await self._judge.label(tc["query"], catalog)
                tc["expected_scenario_ids"] = ids
                tc["_judge_labelled"] = True
                tc["_judge_reason"] = reason
