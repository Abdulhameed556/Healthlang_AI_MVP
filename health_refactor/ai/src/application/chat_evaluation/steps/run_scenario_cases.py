"""Pipeline step: evaluate each scenario agent test case."""
from uuid import UUID

from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.application.retrieval.pipeline import RetrievalPipeline
from ai.src.domain.chat_evaluation.entities import (
    ScenarioCaseResult,
    ScenarioTestCase,
)
from ai.src.domain.chat_system.v1.types import ScenarioAgentInput
from ai.src.infrastructure.chat_evaluation.scorer import KBRelevancyScorer
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent import (
    ScenarioAgent,
)


class RunScenarioCasesStep:
    def __init__(
        self,
        retrieval_pipeline: RetrievalPipeline,
        kb_scorer: KBRelevancyScorer,
    ) -> None:
        self._retrieval = retrieval_pipeline
        self._kb_scorer = kb_scorer

    async def run(self, ctx: ChatEvalContext) -> None:
        agent_id = ctx.agent_id
        if not agent_id:
            raise ValueError("agent_id is required for scenario evaluation")

        scenario_agent = ScenarioAgent()
        name_by_id: dict[str, str] = {
            sid: name for sid, name, *_ in ctx.scenarios_catalog
        }

        for raw in ctx.test_cases:
            tc = ScenarioTestCase(
                query=raw["query"],
                expected_scenario_ids=raw.get("expected_scenario_ids", []),
            )

            routing = await scenario_agent.run(
                ScenarioAgentInput(
                    agent_id=agent_id,
                    user_query=tc.query,
                    message_history=(),
                )
            )

            actual_ids = list(routing.scenario_ids)
            scenario_correct = set(actual_ids) == set(tc.expected_scenario_ids)

            kb_relevancy_score: float | None = None
            if routing.knowledge_base_id and routing.retrieval_query:
                try:
                    chunks = await self._retrieval.retrieve(
                        query=routing.retrieval_query,
                        agent_id=UUID(agent_id),
                    )
                    if chunks:
                        chunk_texts = [c.text for c in chunks]
                        metric = await self._kb_scorer.score(
                            tc.query, chunk_texts
                        )
                        kb_relevancy_score = metric.score
                except Exception:  # noqa: BLE001
                    kb_relevancy_score = None

            ctx.results.append(
                ScenarioCaseResult(
                    query=tc.query,
                    scenario_correct=scenario_correct,
                    actual_scenario_ids=actual_ids,
                    expected_scenario_ids=tc.expected_scenario_ids,
                    kb_relevancy_score=kb_relevancy_score,
                    kb_id_selected=routing.knowledge_base_id,
                    reason=routing.reason,
                    expected_scenario_names=[
                        name_by_id.get(i, i) for i in tc.expected_scenario_ids
                    ],
                    actual_scenario_names=[
                        name_by_id.get(i, i) for i in actual_ids
                    ],
                    judge_labelled=bool(raw.get("_judge_labelled")),
                    judge_reason=raw.get("_judge_reason", ""),
                )
            )
