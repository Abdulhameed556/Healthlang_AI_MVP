"""Orchestrator for the chat pipeline."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from ai.src.application.chat.orchestration_debug import capture_orchestration_turn
from ai.src.application.chat.orchestration_helpers import (
    build_system_prompt,
    format_rules,
    scenarios_prompt_for,
    tool_calls_summary,
)
from ai.src.application.chat.pending_close import (
    DEFAULT_PENDING_CLOSE_GRACE_SECONDS,
    PENDING_CLOSE_STATE,
    apply_pending_close_transition,
)
from ai.src.application.chat.pipeline_logging import (
    log_pipeline_step,
    log_pipeline_timing_summary,
    log_session_facts,
)
from ai.src.application.chat.routing import skipped_scenario_routing
from ai.src.application.chat.session_close import closes_session
from ai.src.application.chat.session_mode import is_test_session
from backend.src.application.integrations.freshchat.session_link import is_freshchat_session
from backend.src.domain.chat_sessions.value_objects import ChatSessionConversationState
from ai.src.application.chat.session_facts import (
    get_session_facts,
    merge_session_facts,
    normalize_session_facts_delta,
    with_session_facts,
)
from ai.src.application.chat.timing import RunTiming
from ai.src.application.chat.types import ChatPipelineInput, ChatPipelineResult
from ai.src.domain.chat.config import ChatConfig
from ai.src.domain.chat_system.v1.types import ScenarioAgentInput
from ai.src.infrastructure.chat_sessions.db_store import (
    ChatSessionClosedError,
    LoadedChatSession,
)
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent import ScenarioAgent
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    load_runtime_for_session,
)
from ai.src.infrastructure.chat_system.v1.guardrails.input_screening import apply_input_screening
from ai.src.infrastructure.chat_system.v1.guardrails.output_screening import apply_output_screening
from ai.src.infrastructure.chat_system.v1.orchestration import (
    DEFAULT_CONFIG,
    build_initial_state,
    compile_chat_graph,
)
from ai.src.infrastructure.chat_system.v1.orchestration.tools.load_agent_tools import (
    describe_tool_resolution,
    orchestration_tool_names,
    resolve_orchestration_tools,
)
from backend.src.domain.chat_sessions.value_objects import ChatSessionStatus
from ai.src.application.retrieval.pipeline import RetrievalPipeline
from ai.src.application.retrieval.dependencies import build_retrieval_pipeline
from ai.src.domain.knowledge_base.entities import DocumentChunk

_background_persist_tasks: set[asyncio.Task[None]] = set()

# Fallback copy when the model closes/transfers but leaves message empty, so the
# customer never sees a blank turn.
_DEFAULT_CLOSING_MESSAGES: dict[str, str] = {
    ChatSessionConversationState.TRANSFER_TO_LIVE_SUPPORT.value: (
        "I've connected you with our live support team — a human agent will continue "
        "with you from here."
    ),
    ChatSessionConversationState.END_CONVERSATION.value: "Glad I could help. Take care!",
}


def _default_closing_message(conversation_state: str) -> str:
    return _DEFAULT_CLOSING_MESSAGES.get(conversation_state, "")


def _format_kb_context(chunks: list[DocumentChunk]) -> str:
    return "\n\n".join(f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(chunks))


@dataclass(frozen=True)
class _TurnPersistRequest:
    session_id: UUID
    user_content: str
    agent_content: str
    conversation_state: str
    previous_conversation_state: str
    user_metadata: dict[str, Any]
    agent_metadata: dict[str, Any]
    session_metadata: dict[str, Any] | None
    cached_loaded: LoadedChatSession
    use_session_cache: bool


class ChatPipeline:
    """Run one chat turn: load session history, orchestrate, persist logs."""

    def __init__(
        self,
        *,
        session_store: ChatSessionStore | None = None,
        retrieval_pipeline: RetrievalPipeline | None = None,
    ) -> None:
        self._session_store = session_store or ChatSessionStore()
        self._retrieval_pipeline = retrieval_pipeline

    async def run(self, pipeline_input: ChatPipelineInput) -> ChatPipelineResult:
        config = pipeline_input.config
        session_id = str(pipeline_input.session_id)
        run_started = time.perf_counter()
        timing = RunTiming()

        log_pipeline_step(session_id, "turn_start", message_len=len(pipeline_input.user_message))

        step_started = time.perf_counter()
        loaded, session_load = await self._session_store.load(
            pipeline_input.session_id,
            use_cache=config.use_session_cache,
        )
        timing.record("session_load", step_started)
        log_pipeline_step(
            session_id,
            "session_load",
            duration_ms=timing.steps["session_load"],
            source=session_load.source,
        )

        chat_session = loaded.session
        if chat_session.status == ChatSessionStatus.CLOSED.value:
            log_pipeline_step(
                session_id,
                "session_closed",
                level="warning",
                close_reason=chat_session.close_reason,
            )
            raise ChatSessionClosedError(
                session_id=session_id,
                closed_at=chat_session.closed_at,
                close_reason=chat_session.close_reason,
            )

        message_history = config.limit_history(loaded.message_history)
        user_query = pipeline_input.user_message
        session_facts = get_session_facts(chat_session.metadata)

        step_started = time.perf_counter()
        runtime, runtime_report = await load_runtime_for_session(chat_session)
        timing.record("runtime_load", step_started)
        log_pipeline_step(
            session_id,
            "runtime_load",
            duration_ms=timing.steps["runtime_load"],
            agent_id=str(runtime.agent_id),
            version_id=str(runtime.version_id),
            version_number=runtime.version_number,
            cache_outcome=runtime_report.cache_outcome,
        )

        rules = format_rules(runtime)

        step_started = time.perf_counter()
        input_screening = await apply_input_screening(
            user_query=user_query,
            message_history=message_history,
            rules=rules,
            enabled=config.enable_input_guardrail,
        )
        timing.record("input_guardrail", step_started)
        screening = input_screening.screening
        log_pipeline_step(
            session_id,
            "input_guardrail",
            duration_ms=timing.steps["input_guardrail"],
            status=input_screening.status,
            enabled=config.enable_input_guardrail,
            provider=screening.provider if screening else None,
            model=screening.model if screening else None,
            blocked=screening.blocked if screening else None,
            parse_success=screening.parse_success if screening else None,
        )

        base_metadata: dict[str, Any] = {
            "session_id": str(pipeline_input.session_id),
            "agent_id": str(runtime.agent_id),
            "version_id": str(runtime.version_id),
            "chat_config": config.to_dict(),
            "session_load": {"source": session_load.source},
            "runtime_load": runtime_report.to_dict(),
            "timing_ms": {},
        }

        if input_screening.status == "block":
            turn_metadata = {
                **base_metadata,
                "input_guardrail": input_screening.to_dict(),
                "pipeline_stopped": "input_guardrail_block",
                "timing_ms": timing.to_dict(),
            }
            delivered = input_screening.message_to_user or ""
            await self._persist_turn(
                session_id=session_id,
                config=config,
                loaded=loaded,
                persist=_TurnPersistRequest(
                    session_id=pipeline_input.session_id,
                    user_content=user_query,
                    agent_content=delivered,
                    conversation_state=chat_session.conversation_state,
                    previous_conversation_state=chat_session.conversation_state,
                    user_metadata={"input_guardrail": input_screening.to_dict()},
                    agent_metadata=turn_metadata,
                    session_metadata=None,
                    cached_loaded=loaded,
                    use_session_cache=config.use_session_cache,
                ),
                timing=timing,
                run_started=run_started,
            )
            timing.record("total", run_started)
            turn_metadata["timing_ms"] = timing.to_dict()
            log_pipeline_step(
                session_id,
                "turn_complete",
                duration_ms=timing.steps["total"],
                outcome="blocked",
                pipeline_stopped="input_guardrail_block",
                level="warning",
                async_persist=config.async_session_persist,
            )
            log_pipeline_timing_summary(session_id, timing.to_dict())
            return ChatPipelineResult(
                session_id=str(pipeline_input.session_id),
                agent_id=str(runtime.agent_id),
                version_id=str(runtime.version_id),
                message=delivered,
                conversation_state=chat_session.conversation_state,
                timing_ms=timing.to_dict(),
                turn_metadata=turn_metadata,
                pipeline_stopped="input_guardrail_block",
            )

        tools = resolve_orchestration_tools(
            runtime,
            use_test_tools=config.use_test_tools,
        )
        tool_names = orchestration_tool_names(tools)
        tool_report = describe_tool_resolution(
            runtime,
            use_test_tools=config.use_test_tools,
        )
        log_pipeline_step(
            session_id,
            "tool_resolution",
            source=tool_report.source,
            bound_tools=tool_report.bound_tool_names,
            tool_count=len(tool_names),
        )

        step_started = time.perf_counter()
        if config.enable_scenario_routing:
            routing = await ScenarioAgent().run(
                ScenarioAgentInput(
                    agent_id=str(runtime.agent_id),
                    user_query=user_query,
                    message_history=message_history,
                    max_scenarios_per_turn=config.max_scenarios_per_turn,
                )
            )
        else:
            routing = skipped_scenario_routing()
        timing.record("scenario_routing", step_started)
        log_pipeline_step(
            session_id,
            "scenario_routing",
            duration_ms=timing.steps["scenario_routing"],
            enabled=config.enable_scenario_routing,
            scenario_ids=list(routing.scenario_ids),
            knowledge_base_id=routing.knowledge_base_id,
            provider=routing.provider,
            model=routing.model,
            parse_success=routing.parse_success,
            reason=routing.reason,
        )

        scenario_prompt = scenarios_prompt_for(runtime, routing.scenario_ids)
        primary_scenario_id = routing.scenario_ids[0] if routing.scenario_ids else None

        knowledge_base_context: str | None = None
        chunks_retrieved = 0
        step_started = time.perf_counter()
        if routing.retrieval_query:
            try:
                retrieval = self._retrieval_pipeline or build_retrieval_pipeline()
                chunks = await retrieval.retrieve(
                    query=routing.retrieval_query,
                    agent_id=runtime.agent_id,
                )
                chunks_retrieved = len(chunks)
                if chunks:
                    knowledge_base_context = _format_kb_context(chunks)
            except Exception as exc:
                log_pipeline_step(
                    session_id, "kb_retrieval", level="warning", error=str(exc)
                )
        timing.record("kb_retrieval", step_started)
        log_pipeline_step(
            session_id,
            "kb_retrieval",
            duration_ms=timing.steps.get("kb_retrieval"),
            retrieval_query=routing.retrieval_query,
            knowledge_base_id=routing.knowledge_base_id,
            chunks_retrieved=chunks_retrieved,
        )

        system_prompt = build_system_prompt(
            runtime,
            scenario_prompt=scenario_prompt,
            rules=rules,
            knowledge_base_context=knowledge_base_context,
            tool_names=tool_names,
            session_conversation_state=chat_session.conversation_state,
            session_facts=session_facts,
            enable_ticket_signal=pipeline_input.external_context is not None,
        )

        state = build_initial_state(
            agent_id=str(runtime.agent_id),
            version_id=str(runtime.version_id),
            system_prompt=system_prompt,
            user_query=user_query,
            message_history=message_history,
            scenario_id=primary_scenario_id,
            knowledge_base_id=routing.knowledge_base_id,
            conversation_state=chat_session.conversation_state,
        )
        graph = compile_chat_graph(
            DEFAULT_CONFIG,
            tools=tools,
            max_llm_calls=config.max_orchestration_llm_calls,
        )
        step_started = time.perf_counter()
        result = await graph.ainvoke(state)
        capture_orchestration_turn(
            session_id=session_id,
            user_query=user_query,
            message_history=message_history,
            system_prompt=system_prompt,
            graph_messages=list(state["messages"]),
            session_conversation_state=chat_session.conversation_state,
            session_facts=session_facts,
            tool_names=tool_names,
            rules=rules,
            scenario_prompt=scenario_prompt,
            routing=routing,
            agent_id=str(runtime.agent_id),
            version_id=str(runtime.version_id),
            scenario_id=primary_scenario_id,
            knowledge_base_id=routing.knowledge_base_id,
            external_source=(
                pipeline_input.external_context.source
                if pipeline_input.external_context
                else None
            ),
            result=result,
        )
        timing.record("orchestration", step_started)
        tool_activity = tool_calls_summary(result["messages"])
        log_pipeline_step(
            session_id,
            "orchestration",
            duration_ms=timing.steps["orchestration"],
            llm_calls=result["llm_calls"],
            parse_success=result.get("parse_success"),
            conversation_state=result.get("conversation_state"),
            tool_activity=tool_activity,
            message_preview=(result.get("assistant_message") or "")[:160],
        )

        assistant_message = result["assistant_message"] or ""
        step_started = time.perf_counter()
        output_screening = await apply_output_screening(
            user_query=user_query,
            assistant_message=assistant_message,
            message_history=message_history,
            rules=rules,
            tools_used=tool_names,
            agent_name=runtime.agent_name,
            brand_config=runtime.brand_config,
            personalization_config=runtime.personalization_config,
            enabled=config.enable_output_guardrail,
        )
        timing.record("output_guardrail", step_started)
        output_screening_result = output_screening.screening
        log_pipeline_step(
            session_id,
            "output_guardrail",
            duration_ms=timing.steps["output_guardrail"],
            status=output_screening.status,
            enabled=config.enable_output_guardrail,
            provider=output_screening_result.provider if output_screening_result else None,
            model=output_screening_result.model if output_screening_result else None,
            action=output_screening_result.action.value
            if output_screening_result and output_screening_result.action
            else None,
        )

        conversation_state = result["conversation_state"]
        facts_delta = normalize_session_facts_delta(result.get("session_facts", {}))
        merged_session_facts = merge_session_facts(session_facts, facts_delta)
        log_session_facts(
            session_id,
            previous=session_facts,
            delta=facts_delta,
            merged=merged_session_facts,
        )
        session_metadata = with_session_facts(chat_session.metadata, merged_session_facts)
        session_metadata = apply_pending_close_transition(
            session_metadata,
            previous_state=chat_session.conversation_state,
            new_state=conversation_state,
        )
        delivered = output_screening.message_to_user or ""
        if closes_session(conversation_state) and not delivered.strip():
            delivered = _default_closing_message(conversation_state)
        turn_metadata = {
            **base_metadata,
            "scenario_id": result["scenario_id"],
            "knowledge_base_id": result["knowledge_base_id"],
            "llm_calls": result["llm_calls"],
            "input_guardrail": input_screening.to_dict(),
            "output_guardrail": output_screening.to_dict(),
            "session_facts": {
                "previous": session_facts,
                "delta": facts_delta,
                "merged": merged_session_facts,
            },
            "routing": {
                "scenario_ids": list(routing.scenario_ids),
                "scenario_id": primary_scenario_id,
                "knowledge_base_id": routing.knowledge_base_id,
                "rule_ids": list(routing.rule_ids),
                "retrieval_query": routing.retrieval_query,
                "experience_queries": list(routing.experience_queries),
                "reason": routing.reason,
                "chunks_retrieved": chunks_retrieved,
            },
            "orchestration": {
                "assistant_message_raw": assistant_message,
                "parse_success": result["parse_success"],
                "tool_activity": tool_calls_summary(result["messages"]),
                "ticket_action": result.get("ticket_action"),
                "ticket_reason": result.get("ticket_reason"),
                "issue_resolved": result.get("issue_resolved"),
            },
            "tool_resolution": {
                "source": tool_report.source,
                "bound_tools": list(tool_report.bound_tool_names),
            },
            "timing_ms": timing.to_dict(),
        }

        await self._persist_turn(
            session_id=session_id,
            config=config,
            loaded=loaded,
            persist=_TurnPersistRequest(
                session_id=pipeline_input.session_id,
                user_content=user_query,
                agent_content=delivered,
                conversation_state=conversation_state,
                previous_conversation_state=chat_session.conversation_state,
                user_metadata={"input_guardrail": input_screening.to_dict()},
                agent_metadata=turn_metadata,
                session_metadata=session_metadata,
                cached_loaded=loaded,
                use_session_cache=config.use_session_cache,
            ),
            timing=timing,
            run_started=run_started,
        )
        timing.record("total", run_started)
        turn_metadata["timing_ms"] = timing.to_dict()

        log_pipeline_step(
            session_id,
            "turn_complete",
            duration_ms=timing.steps["total"],
            outcome="ok",
            conversation_state=conversation_state,
            delivered_len=len(delivered),
            async_persist=config.async_session_persist,
        )
        log_pipeline_timing_summary(session_id, timing.to_dict())

        return ChatPipelineResult(
            session_id=str(pipeline_input.session_id),
            agent_id=str(runtime.agent_id),
            version_id=str(runtime.version_id),
            message=delivered,
            conversation_state=conversation_state,
            timing_ms=timing.to_dict(),
            turn_metadata=turn_metadata,
        )

    async def _persist_turn(
        self,
        *,
        session_id: str,
        config: ChatConfig,
        loaded: LoadedChatSession,
        persist: _TurnPersistRequest,
        timing: RunTiming,
        run_started: float,
    ) -> None:
        if config.async_session_persist:
            cache_started = time.perf_counter()
            if persist.use_session_cache:
                await self._session_store.warm_cache_for_turn(
                    session_id=persist.session_id,
                    user_content=persist.user_content,
                    agent_content=persist.agent_content,
                    conversation_state=persist.conversation_state,
                    session_metadata=persist.session_metadata,
                    cached_loaded=persist.cached_loaded,
                )
            timing.record("cache_warm", cache_started)
            log_pipeline_step(
                session_id,
                "cache_warm",
                duration_ms=timing.steps.get("cache_warm"),
                async_persist=True,
            )
            self._schedule_database_persist(session_id=session_id, persist=persist)
            return

        step_started = time.perf_counter()
        await self._session_store.append_turn(
            session_id=persist.session_id,
            user_content=persist.user_content,
            agent_content=persist.agent_content,
            conversation_state=persist.conversation_state,
            user_metadata=persist.user_metadata,
            agent_metadata=persist.agent_metadata,
            session_metadata=persist.session_metadata,
            cached_loaded=loaded,
            use_cache=config.use_session_cache,
            chat_session=loaded.session,
            next_sequence_index=len(loaded.message_history),
        )
        timing.record("persist_turn", step_started)
        log_pipeline_step(
            session_id,
            "persist_turn",
            duration_ms=timing.steps["persist_turn"],
            async_persist=False,
        )
        self._enqueue_post_close_if_closing(session_id=session_id, persist=persist)
        self._enqueue_close_check_if_entering_pending_close(
            session_id=session_id, persist=persist
        )

    def _schedule_database_persist(
        self,
        *,
        session_id: str,
        persist: _TurnPersistRequest,
    ) -> None:
        task = asyncio.create_task(
            self._persist_turn_to_database(session_id=session_id, persist=persist),
            name=f"chat-persist-{session_id}",
        )
        _background_persist_tasks.add(task)
        task.add_done_callback(_background_persist_tasks.discard)

    async def _persist_turn_to_database(
        self,
        *,
        session_id: str,
        persist: _TurnPersistRequest,
    ) -> None:
        step_started = time.perf_counter()
        try:
            await self._session_store.append_turn_to_database(
                session_id=persist.session_id,
                user_content=persist.user_content,
                agent_content=persist.agent_content,
                conversation_state=persist.conversation_state,
                user_metadata=persist.user_metadata,
                agent_metadata=persist.agent_metadata,
                session_metadata=persist.session_metadata,
                chat_session=persist.cached_loaded.session,
                next_sequence_index=len(persist.cached_loaded.message_history),
            )
            duration_ms = (time.perf_counter() - step_started) * 1000
            log_pipeline_step(
                session_id,
                "persist_turn",
                duration_ms=duration_ms,
                async_persist=True,
            )
            self._enqueue_post_close_if_closing(session_id=session_id, persist=persist)
            self._enqueue_close_check_if_entering_pending_close(
                session_id=session_id, persist=persist
            )
        except Exception as exc:
            duration_ms = (time.perf_counter() - step_started) * 1000
            log_pipeline_step(
                session_id,
                "persist_turn",
                duration_ms=duration_ms,
                async_persist=True,
                outcome="error",
                error=str(exc),
                level="error",
            )

    def _enqueue_post_close_if_closing(
        self,
        *,
        session_id: str,
        persist: _TurnPersistRequest,
    ) -> None:
        """Queue the post-close ticketing pipeline once a closing turn is persisted.

        Only ``end_conversation`` / ``transfer_to_live_support`` close the session
        synchronously; for those we enqueue here, after the close is durable in the
        DB, so the worker (which reads the DB) does not race the write. A broker
        failure must not break the already-delivered turn, so we log and move on.
        """
        if not closes_session(persist.conversation_state):
            return
        session_metadata = persist.session_metadata or persist.cached_loaded.session.metadata
        if is_test_session(session_metadata):
            log_pipeline_step(
                session_id,
                "post_close_enqueue",
                conversation_state=persist.conversation_state,
                outcome="skipped",
                reason="test_session",
            )
            return
        if is_freshchat_session(session_metadata):
            # Freshchat inbound tickets synchronously on end/transfer; enqueueing
            # post_close here raced that path and produced duplicate tickets.
            log_pipeline_step(
                session_id,
                "post_close_enqueue",
                conversation_state=persist.conversation_state,
                outcome="skipped",
                reason="freshchat_inbound_ticketing",
            )
            return
        try:
            from ai.src.infrastructure.workers.enqueue import enqueue_post_close_pipeline

            enqueue_post_close_pipeline(persist.session_id)
            log_pipeline_step(
                session_id,
                "post_close_enqueue",
                conversation_state=persist.conversation_state,
            )
        except Exception as exc:
            log_pipeline_step(
                session_id,
                "post_close_enqueue",
                conversation_state=persist.conversation_state,
                outcome="error",
                error=str(exc),
                level="error",
            )

    def _enqueue_close_check_if_entering_pending_close(
        self,
        *,
        session_id: str,
        persist: _TurnPersistRequest,
    ) -> None:
        """Queue the delayed grace-timeout check when a turn enters pending_close.

        Only fire on the *transition* into ``pending_close`` (not on every turn
        that stays pending), so the grace deadline stamped on this turn is not
        repeatedly re-scheduled. The check is enqueued after the deadline metadata
        is durable in the DB. A broker failure must not break the delivered turn.
        """
        entering_pending_close = (
            persist.conversation_state == PENDING_CLOSE_STATE
            and persist.previous_conversation_state != PENDING_CLOSE_STATE
        )
        if not entering_pending_close:
            return
        try:
            from ai.src.infrastructure.workers.enqueue import enqueue_session_close_check

            enqueue_session_close_check(
                persist.session_id,
                delay_ms=DEFAULT_PENDING_CLOSE_GRACE_SECONDS * 1000,
            )
            log_pipeline_step(
                session_id,
                "session_close_check_enqueue",
                delay_seconds=DEFAULT_PENDING_CLOSE_GRACE_SECONDS,
            )
        except Exception as exc:
            log_pipeline_step(
                session_id,
                "session_close_check_enqueue",
                outcome="error",
                error=str(exc),
                level="error",
            )
