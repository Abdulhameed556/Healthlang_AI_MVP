"""Pipeline step: run all 4 chat stages per test case and score with DeepEval."""
from uuid import UUID

from ai.src.application.chat.orchestration_helpers import (
    build_system_prompt,
    format_rules,
    scenarios_prompt_for,
)
from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.application.retrieval.pipeline import RetrievalPipeline
from ai.src.domain.chat_evaluation.entities import E2ETestCase, E2ETurnResult
from ai.src.domain.chat_system.v1.types import (
    ConversationSessionState,
    ScenarioAgentInput,
)
from ai.src.infrastructure.chat_evaluation.scorer import E2EScorer
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent import ScenarioAgent
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    load_scenario_runtime,
)
from ai.src.infrastructure.chat_system.v1.guardrails.input_screening import (
    apply_input_screening,
)
from ai.src.infrastructure.chat_system.v1.guardrails.output_screening import (
    apply_output_screening,
)
from ai.src.infrastructure.chat_system.v1.orchestration import DEFAULT_CONFIG
from ai.src.infrastructure.chat_system.v1.orchestration.graph import compile_chat_graph
from ai.src.infrastructure.chat_system.v1.orchestration.state import build_initial_state


def _format_kb_context(chunks: list) -> str:
    return "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks))


class RunE2ECasesStep:
    def __init__(self, retrieval_pipeline: RetrievalPipeline, e2e_scorer: E2EScorer) -> None:
        self._retrieval = retrieval_pipeline
        self._scorer = e2e_scorer

    async def run(self, ctx: ChatEvalContext) -> None:
        agent_id = ctx.agent_id
        if not agent_id:
            raise ValueError("agent_id is required for e2e evaluation")

        runtime = await load_scenario_runtime(UUID(agent_id))
        graph = compile_chat_graph(DEFAULT_CONFIG)

        for raw in ctx.test_cases:
            tc = E2ETestCase(query=raw["query"], expected_answer=raw["expected_answer"])

            # Stage 1 — input guardrail
            input_screen = await apply_input_screening(user_query=tc.query, enabled=True)
            if input_screen.status == "block":
                ctx.results.append(
                    E2ETurnResult(
                        query=tc.query,
                        expected_answer=tc.expected_answer,
                        actual_response="",
                        input_guardrail_status="block",
                        scenario_ids=[],
                        kb_id_selected=None,
                        chunks_retrieved=0,
                        output_guardrail_status="skipped",
                        pipeline_stopped="input_guardrail_block",
                    )
                )
                continue

            # Stage 2 — scenario routing
            routing = await ScenarioAgent().run(
                ScenarioAgentInput(agent_id=agent_id, user_query=tc.query)
            )

            # Stage 3 — KB retrieval
            chunks: list = []
            if routing.retrieval_query:
                try:
                    chunks = await self._retrieval.retrieve(
                        query=routing.retrieval_query,
                        agent_id=UUID(agent_id),
                    )
                except Exception:
                    chunks = []

            retrieval_context = [c.text for c in chunks]
            knowledge_base_context = _format_kb_context(chunks) if chunks else None
            scenario_prompt = scenarios_prompt_for(runtime, routing.scenario_ids)
            primary_scenario_id = routing.scenario_ids[0] if routing.scenario_ids else None

            # Stage 4 — orchestration (no tools in eval mode for isolation)
            system_prompt = build_system_prompt(
                runtime,
                scenario_prompt=scenario_prompt,
                rules=format_rules(runtime),
                knowledge_base_context=knowledge_base_context,
                tool_names=(),
                session_conversation_state=ConversationSessionState.IN_PROGRESS.value,
                session_facts={},
            )
            state = build_initial_state(
                agent_id=agent_id,
                version_id=str(runtime.version_id),
                system_prompt=system_prompt,
                user_query=tc.query,
                scenario_id=primary_scenario_id,
                knowledge_base_id=routing.knowledge_base_id,
            )
            graph_result = await graph.ainvoke(state)
            assistant_message = graph_result.get("assistant_message") or ""

            # Stage 5 — output guardrail
            output_screen = await apply_output_screening(
                user_query=tc.query,
                assistant_message=assistant_message,
                enabled=True,
            )
            final_message = output_screen.message_to_user

            # DeepEval scoring
            metrics = await self._scorer.score(
                query=tc.query,
                actual_output=final_message,
                expected_output=tc.expected_answer,
                retrieval_context=retrieval_context,
            )

            ctx.results.append(
                E2ETurnResult(
                    query=tc.query,
                    expected_answer=tc.expected_answer,
                    actual_response=final_message,
                    input_guardrail_status=input_screen.status,
                    scenario_ids=list(routing.scenario_ids),
                    kb_id_selected=routing.knowledge_base_id,
                    chunks_retrieved=len(chunks),
                    output_guardrail_status=output_screen.status,
                    metrics=metrics,
                )
            )
