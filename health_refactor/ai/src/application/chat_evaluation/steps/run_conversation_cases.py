"""Replay generated conversations through the real agent pipeline."""
from __future__ import annotations

import asyncio
from uuid import UUID

from ai.src.application.chat.orchestration_helpers import (
    build_system_prompt,
    format_rules,
    scenarios_prompt_for,
)
from ai.src.application.chat_evaluation.context import ChatEvalContext
from ai.src.application.retrieval.pipeline import RetrievalPipeline
from ai.src.domain.chat_evaluation.entities import (
    ConversationCaseResult,
    ConversationTurn,
)
from ai.src.domain.chat_system.v1.types import (
    ConversationSessionState,
    ScenarioAgentInput,
)
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_evaluation.conversation_scorer import (
    ConversationScorer,
)
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent import (
    ScenarioAgent,
)
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (  # noqa: E501
    load_scenario_runtime,
)
from ai.src.infrastructure.chat_system.v1.guardrails.input_screening import (
    apply_input_screening,
)
from ai.src.infrastructure.chat_system.v1.guardrails.output_screening import (
    apply_output_screening,
)
from ai.src.infrastructure.chat_system.v1.orchestration import DEFAULT_CONFIG
from ai.src.infrastructure.chat_system.v1.orchestration.graph import (
    compile_chat_graph,
)
from ai.src.infrastructure.chat_system.v1.orchestration.state import (
    build_initial_state,
)
from ai.src.infrastructure.chat_system.v1.orchestration.tools.load_agent_tools import (  # noqa: E501
    load_agent_tools,
    load_agent_tools_with_mocks,
)


def _format_kb_context(chunks: list) -> str:
    return "\n\n".join(f"[{i + 1}] {c.text}" for i, c in enumerate(chunks))


class RunConversationCasesStep:
    def __init__(
        self,
        retrieval_pipeline: RetrievalPipeline,
        scorer: ConversationScorer,
    ) -> None:
        self._retrieval = retrieval_pipeline
        self._scorer = scorer

    async def run(self, ctx: ChatEvalContext) -> None:
        agent_id = ctx.agent_id
        if not agent_id:
            raise ValueError(
                "agent_id is required for conversation evaluation"
            )

        runtime = await load_scenario_runtime(UUID(agent_id))
        rules = list(format_rules(runtime))
        kb_descriptions = [
            kb.description or kb.name for kb in runtime.knowledge_bases
        ]

        if not ctx.conversations:
            return

        api_tool_mocks = getattr(ctx, "api_tool_mocks", None)
        if api_tool_mocks:
            tools = load_agent_tools_with_mocks(
                runtime, mock_responses=api_tool_mocks
            )
        elif api_tool_mocks is not None:
            tools = load_agent_tools(runtime)
        else:
            tools = []

        first_speaker = getattr(ctx, "first_speaker", None)
        welcome_text = getattr(ctx, "welcome_message", None)
        initial_history: list[ChatMessage] = (
            [ChatMessage(role=MessageRole.ASSISTANT, content=welcome_text)]
            if first_speaker == "agent" and welcome_text
            else []
        )

        graph = compile_chat_graph(DEFAULT_CONFIG, tools=tools)
        scenario_agent = ScenarioAgent()

        tasks = [
            self._run_single(
                agent_id=agent_id,
                conv=conv,
                run_idx=run_idx,
                runtime=runtime,
                rules=rules,
                kb_descriptions=kb_descriptions,
                graph=graph,
                scenario_agent=scenario_agent,
                tools=tools,
                initial_history=initial_history,
            )
            for conv in ctx.conversations
            for run_idx in range(ctx.determinism_runs)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, BaseException):
                continue
            ctx.results.append(result)

    async def _run_single(
        self,
        *,
        agent_id: str,
        conv: dict,
        run_idx: int,
        runtime,
        rules: list[str],
        kb_descriptions: list[str],
        graph,
        scenario_agent: ScenarioAgent,
        tools: list,
        initial_history: list[ChatMessage],
    ) -> ConversationCaseResult:
        turns_raw: list[dict] = conv.get("turns", [])
        executed_turns: list[ConversationTurn] = []
        message_history: list[ChatMessage] = list(initial_history)
        scored_turns: list[dict] = []

        for turn_raw in turns_raw:
            user_msg = str(turn_raw.get("user", "")).strip()
            agent_expected = str(turn_raw.get("agent_expected", "")).strip()
            if not user_msg:
                continue

            # Stage 1 — input guardrail
            input_screen = await apply_input_screening(
                user_query=user_msg, enabled=True
            )
            if input_screen.status == "block":
                executed_turns.append(
                    ConversationTurn(
                        user=user_msg,
                        agent_expected=agent_expected,
                        agent_actual="[blocked by input guardrail]",
                        input_guardrail_status="block",
                        output_guardrail_status="skipped",
                    )
                )
                scored_turns.append(
                    {
                        "user": user_msg,
                        "agent_actual": "[blocked by input guardrail]",
                    }
                )
                message_history.append(
                    ChatMessage(role=MessageRole.USER, content=user_msg)
                )
                message_history.append(
                    ChatMessage(
                        role=MessageRole.ASSISTANT,
                        content="[blocked by input guardrail]",
                    )
                )
                continue

            # Stage 2 — scenario routing (with accumulated history)
            routing = await scenario_agent.run(
                ScenarioAgentInput(
                    agent_id=agent_id,
                    user_query=user_msg,
                    message_history=tuple(message_history),
                )
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

            knowledge_base_context = (
                _format_kb_context(chunks) if chunks else None
            )
            scenario_prompt = scenarios_prompt_for(
                runtime, routing.scenario_ids
            )
            primary_scenario_id = (
                routing.scenario_ids[0] if routing.scenario_ids else None
            )

            # Stage 4 — orchestration
            system_prompt = build_system_prompt(
                runtime,
                scenario_prompt=scenario_prompt,
                rules=tuple(rules),
                knowledge_base_context=knowledge_base_context,
                tool_names=tuple(t.name for t in tools),
                session_conversation_state=(
                    ConversationSessionState.IN_PROGRESS.value
                ),
                session_facts={},
            )
            state = build_initial_state(
                agent_id=agent_id,
                version_id=str(runtime.version_id),
                system_prompt=system_prompt,
                user_query=user_msg,
                message_history=tuple(message_history),
                scenario_id=primary_scenario_id,
                knowledge_base_id=routing.knowledge_base_id,
            )
            graph_result = await graph.ainvoke(state)
            agent_actual = graph_result.get("assistant_message") or ""

            # Stage 5 — output guardrail
            output_screen = await apply_output_screening(
                user_query=user_msg,
                assistant_message=agent_actual,
                enabled=True,
            )
            final_message = output_screen.message_to_user

            executed_turns.append(
                ConversationTurn(
                    user=user_msg,
                    agent_expected=agent_expected,
                    agent_actual=final_message,
                    input_guardrail_status=input_screen.status,
                    output_guardrail_status=output_screen.status,
                    scenario_ids=list(routing.scenario_ids),
                    kb_id_selected=routing.knowledge_base_id,
                )
            )
            scored_turns.append(
                {"user": user_msg, "agent_actual": final_message}
            )

            message_history.append(
                ChatMessage(role=MessageRole.USER, content=user_msg)
            )
            message_history.append(
                ChatMessage(role=MessageRole.ASSISTANT, content=final_message)
            )

        # Score the full conversation with GEval
        scenario_description = conv.get("scenario_name", "")
        metric_results = []
        if scored_turns:
            try:
                metric_results = await self._scorer.score(
                    scenario_description=scenario_description,
                    conversation_turns=scored_turns,
                    rules=rules,
                    kb_descriptions=kb_descriptions,
                )
            except Exception as exc:
                from ai.src.domain.chat_evaluation.entities import MetricResult
                metric_results = [
                    MetricResult(
                        name="conversation_quality",
                        score=0.0,
                        threshold=0.5,
                        success=False,
                        reason=f"scorer error: {exc}",
                    )
                ]

        scores = {m.name: m.score for m in metric_results}

        return ConversationCaseResult(
            scenario_id=conv.get("scenario_id", ""),
            scenario_name=conv.get("scenario_name", ""),
            persona=conv.get("persona", ""),
            run_index=run_idx,
            turns=executed_turns,
            scores=scores,
        )
