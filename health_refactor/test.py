"""Chat orchestration graph smoke test.

Run from repo root:

    python test.py
    python test.py --query "What is your refund policy?"
    python test.py --no-tools
    python test.py --session-id <uuid> --query "Hello"
    python test.py --new-session --agent-id <uuid> --query "Hello"

Prints runtime-load trace and per-phase timing (ms).
Use --verbose for application logs plus orchestration trace.

Inputs (edit constants below)
-----------------------------
- AGENT_ID — loads deployed agent version from Postgres
- USER_QUERY — latest user message
- MESSAGE_HISTORY — prior turns
- SESSION_CONVERSATION_STATE — prior session state (Redis later)
- Chat pipeline toggles — edit ai/src/application/chat/settings.py (override via CLI)
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from uuid import UUID

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from ai.src.application.chat.settings import (
    DEFAULT_AGENT_ID,
    add_chat_config_arguments,
    chat_config_from_cli_args,
)
from ai.src.domain.chat_system.v1.types import ConversationSessionState
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent import ScenarioAgent
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    load_scenario_runtime_with_report,
)
from ai.src.infrastructure.chat_system.v1.orchestration import (
    DEFAULT_CONFIG,
    build_initial_state,
    compile_chat_graph,
    load_prompt_module,
)
from ai.src.infrastructure.chat_system.v1.orchestration.prompt_context import build_prompt_context
from ai.src.infrastructure.chat_system.v1.orchestration.response import parse_orchestration_turn
from ai.src.infrastructure.chat_system.v1.orchestration.tools.load_agent_tools import (
    describe_tool_resolution,
    orchestration_tool_names,
    resolve_orchestration_tools,
)
from ai.src.infrastructure.chat_system.v1.guardrails.input_screening import (
    apply_input_screening,
)
from ai.src.infrastructure.chat_system.v1.guardrails.output_screening import (
    apply_output_screening,
)
from ai.src.infrastructure.llm.providers.langchain_helpers import extract_message_text

# ---------------------------------------------------------------------------
# Edit these
# ---------------------------------------------------------------------------

AGENT_ID = DEFAULT_AGENT_ID

USER_QUERY = "can i get info about customer id 2 from public api and how di reach him?"

MESSAGE_HISTORY: tuple[ChatMessage, ...] = (
    ChatMessage(role=MessageRole.USER, content="Hi, I need help with an order."),
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content="Sure — tell me what happened with the order.",
    ),
)

SESSION_CONVERSATION_STATE = ConversationSessionState.IN_PROGRESS.value


def _format_rules(runtime) -> tuple[str, ...]:
    return tuple(
        f"{rule.name}: {rule.description}" for rule in runtime.rules if rule.description
    )


def _scenarios_prompt_for(runtime, scenario_ids: tuple[str, ...]) -> str | None:
    if not scenario_ids:
        return None
    by_id = {str(scenario.id): scenario for scenario in runtime.scenarios}
    sections: list[str] = []
    for scenario_id in scenario_ids:
        scenario = by_id.get(scenario_id)
        if scenario and scenario.prompt.strip():
            title = scenario.name.strip() or scenario_id
            sections.append(f"Scenario: {title}\n{scenario.prompt.strip()}")
    return "\n\n".join(sections) if sections else None


def _build_system_prompt(
    runtime,
    *,
    scenario_prompt: str | None,
    rules: tuple[str, ...],
    knowledge_base_context: str | None,
    tool_names: tuple[str, ...],
    session_conversation_state: str,
    session_facts: dict[str, str] | None = None,
) -> str:
    prompts = load_prompt_module(DEFAULT_CONFIG.prompt_version)
    ctx = build_prompt_context(
        runtime,
        scenario_prompt=scenario_prompt,
        knowledge_base_context=knowledge_base_context,
        tool_names=tool_names,
        session_conversation_state=session_conversation_state,
        session_facts=session_facts,
    )
    return prompts.build_system_prompt(ctx)


def _tool_calls_summary(messages: list) -> list[dict]:
    summary: list[dict] = []
    for message in messages:
        if isinstance(message, AIMessage) and message.tool_calls:
            for call in message.tool_calls:
                summary.append({"name": call["name"], "args": call["args"]})
        if isinstance(message, ToolMessage):
            summary.append({"tool_result": message.content[:120]})
    return summary


def _orchestration_trace(messages: list, *, preview_chars: int = 300) -> list[dict]:
    """Step-by-step trace of LLM turns and tool activity."""
    trace: list[dict] = []
    llm_turn = 0
    for index, message in enumerate(messages):
        if isinstance(message, SystemMessage):
            trace.append(
                {
                    "step": "system_prompt",
                    "message_index": index,
                    "preview": (message.content or "")[:preview_chars],
                }
            )
            continue
        if isinstance(message, HumanMessage):
            trace.append(
                {
                    "step": "history_or_user",
                    "message_index": index,
                    "content": message.content,
                }
            )
            continue
        if isinstance(message, AIMessage):
            llm_turn += 1
            entry: dict = {
                "step": "llm_turn",
                "turn": llm_turn,
                "message_index": index,
                "tool_calls": [
                    {"name": call["name"], "args": call.get("args", {})}
                    for call in (message.tool_calls or [])
                ],
            }
            if not message.tool_calls:
                raw_text = extract_message_text(message)
                parsed = parse_orchestration_turn(raw_text)
                entry["raw_output_preview"] = raw_text[:preview_chars]
                entry["parse_success"] = parsed.parse_success
                entry["parsed_message_preview"] = parsed.message[:preview_chars]
                entry["parsed_conversation_state"] = parsed.conversation_state.value
            trace.append(entry)
            continue
        if isinstance(message, ToolMessage):
            trace.append(
                {
                    "step": "tool_result",
                    "message_index": index,
                    "tool_call_id": message.tool_call_id,
                    "content_preview": (message.content or "")[:preview_chars],
                }
            )
    return trace


def _print_runtime_load(report, *, elapsed_ms: float | None = None) -> None:
    print("=== Runtime load ===")
    if report.version_id is not None:
        suffix = f" ({elapsed_ms:.0f}ms)" if elapsed_ms is not None else ""
        print(
            f"Deployed: v{report.version_number} ({report.version_id}) "
            f"| cache: {report.cache_outcome}{suffix}"
        )
    elif elapsed_ms is not None:
        print(f"Cache: {report.cache_outcome} ({elapsed_ms:.0f}ms)")
    else:
        print(f"Cache: {report.cache_outcome}")
    for step in report.steps:
        print(f"  [{step.name}] {step.detail}")
    print()


@dataclass
class RunTiming:
    """Elapsed milliseconds for major smoke-test phases."""

    steps: dict[str, float] = field(default_factory=dict)

    def record(self, name: str, started_at: float) -> None:
        self.steps[name] = (time.perf_counter() - started_at) * 1000

    def to_dict(self) -> dict[str, float]:
        return {name: round(ms, 1) for name, ms in self.steps.items()}


def _print_timing(timing: RunTiming) -> None:
    print("=== Timing ===")
    for name, ms in timing.steps.items():
        if name == "total":
            continue
        print(f"  {name}: {ms:.0f}ms")
    if "total" in timing.steps:
        print(f"  total: {timing.steps['total']:.0f}ms")
    print()


def _print_input_screening(report, *, elapsed_ms: float | None = None) -> None:
    print("=== Input guardrail ===")
    suffix = f" ({elapsed_ms:.0f}ms)" if elapsed_ms is not None else ""
    print(f"Status: {report.status}{suffix}")
    if report.status == "block":
        print(f"  attack: {report.attack_category}")
        print(f"  reason: {report.blocked_reason}")
        print(f"  delivered: {report.message_to_user!r}")
    elif report.status == "pass" and report.screening is not None:
        print(
            f"  model: {report.screening.provider}/{report.screening.model} "
            f"| parse_success: {report.screening.parse_success}"
        )
    elif report.status == "skipped":
        print("  guardrail disabled or empty user query")
    print()


def _print_output_screening(report, *, elapsed_ms: float | None = None) -> None:
    print("=== Output guardrail ===")
    suffix = f" ({elapsed_ms:.0f}ms)" if elapsed_ms is not None else ""
    print(f"Status: {report.status}{suffix}")
    if report.status == "block":
        print(f"  violation: {report.violation_category}")
        print(f"  reason: {report.blocked_reason}")
        print(f"  delivered: {report.message_to_user!r}")
        if report.original_message:
            preview = report.original_message[:120]
            print(f"  blocked_original: {preview!r}")
    elif report.status == "reformat":
        print(f"  violation: {report.violation_category}")
        print(f"  reason: {report.blocked_reason}")
        print(f"  delivered: {report.message_to_user!r}")
        if report.original_message:
            preview = report.original_message[:120]
            print(f"  original: {preview!r}")
    elif report.status == "pass" and report.screening is not None:
        print(
            f"  model: {report.screening.provider}/{report.screening.model} "
            f"| parse_success: {report.screening.parse_success}"
        )
    elif report.status == "skipped":
        print("  guardrail disabled or empty assistant message")
    print()


def _print_tool_resolution(report) -> None:
    print("=== Tool resolution ===")
    print(f"Source: {report.source}")
    print(f"Bound tools: {', '.join(report.bound_tool_names) or 'none'}")
    if report.deployed_tools:
        print("Deployed API tools on this agent version:")
        for tool in report.deployed_tools:
            print(f"  - {tool['name']} ({tool['http_method']} {tool['endpoint_url']})")
    else:
        print("Deployed API tools on this agent version: none")
    if report.source == "test_fallback":
        print(
            "\nNOTE: Fell back to local get_company_doc because the deployed version "
            "has no API tools loaded."
        )
        print(
            "      If you attached tools in the dashboard, redeploy the agent so "
            "api_tool_ids are in the deployed snapshot."
        )
    print()


def _print_orchestration_trace(trace: list[dict]) -> None:
    print("=== Orchestration trace ===")
    for entry in trace:
        step = entry["step"]
        if step == "system_prompt":
            print(f"[system] prompt preview: {entry['preview']!r}")
        elif step == "history_or_user":
            print(f"[user/history] {entry['content']!r}")
        elif step == "llm_turn":
            if entry["tool_calls"]:
                print(f"[llm turn {entry['turn']}] requested tools:")
                for call in entry["tool_calls"]:
                    print(f"  - {call['name']} args={json.dumps(call['args'])}")
            else:
                print(f"[llm turn {entry['turn']}] final reply (no tool calls)")
                print(f"  parse_success: {entry['parse_success']}")
                print(f"  raw_output: {entry['raw_output_preview']!r}")
                if not entry["parse_success"]:
                    print(
                        "  hint: model must return JSON "
                        '{"message": "...", "conversation_state": "in_progress"}'
                    )
        elif step == "tool_result":
            print(
                f"[tool result] call_id={entry['tool_call_id']} "
                f"content={entry['content_preview']!r}"
            )
    print()


async def _run_session_pipeline(args) -> int:
    from ai.src.application.chat.pipeline import ChatPipeline
    from ai.src.application.chat.types import ChatPipelineInput
    from ai.src.infrastructure.chat_sessions.store import ChatSessionStore

    store = ChatSessionStore()
    chat_config = chat_config_from_cli_args(args)
    if args.new_session:
        runtime, _report = await load_scenario_runtime_with_report(UUID(args.agent_id))
        session = await store.create(
            organization_id=runtime.organization_id,
            agent_id=runtime.agent_id,
            agent_version_id=runtime.version_id,
            use_cache=chat_config.use_session_cache,
        )
        session_id = session.id
        print(f"Created session: {session_id}\n")
    else:
        session_id = UUID(args.session_id)

    user_query = args.query or USER_QUERY

    pipeline = ChatPipeline(session_store=store)
    result = await pipeline.run(
        ChatPipelineInput(
            session_id=session_id,
            user_message=user_query,
            config=chat_config,
        )
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0 if result.message else 1


async def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test chat orchestration graph.")
    parser.add_argument("--agent-id", default=AGENT_ID, help="Deployed agent UUID.")
    parser.add_argument("--query", help="Override USER_QUERY for this run.")
    add_chat_config_arguments(parser)
    parser.add_argument(
        "--session-id",
        help="Run ChatPipeline for an existing session (loads history from DB).",
    )
    parser.add_argument(
        "--new-session",
        action="store_true",
        help="Create a chat_sessions row, then run the pipeline for --query.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print orchestration trace (LLM turns, tool calls, raw output).",
    )
    args = parser.parse_args()

    if args.session_id or args.new_session:
        return await _run_session_pipeline(args)

    run_started = time.perf_counter()
    timing = RunTiming()

    if args.verbose:
        logging.basicConfig(
            level=logging.INFO,
            format="%(levelname)s [%(name)s] %(message)s",
            force=True,
        )
        logging.getLogger("backend.src.infrastructure.agent_runtime").setLevel(logging.INFO)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    chat_config = chat_config_from_cli_args(args)
    user_query = args.query or USER_QUERY
    message_history = chat_config.limit_history(MESSAGE_HISTORY)

    step_started = time.perf_counter()
    runtime, runtime_report = await load_scenario_runtime_with_report(UUID(args.agent_id))
    timing.record("runtime_load", step_started)
    _print_runtime_load(runtime_report, elapsed_ms=timing.steps["runtime_load"])

    rules = _format_rules(runtime)

    step_started = time.perf_counter()
    input_screening = await apply_input_screening(
        user_query=user_query,
        message_history=message_history,
        rules=rules,
        enabled=chat_config.enable_input_guardrail,
    )
    timing.record("input_guardrail", step_started)
    _print_input_screening(
        input_screening,
        elapsed_ms=timing.steps.get("input_guardrail"),
    )

    if input_screening.status == "block":
        timing.record("total", run_started)
        _print_timing(timing)
        payload = {
            "agent_id": str(runtime.agent_id),
            "version_id": str(runtime.version_id),
            "input_guardrail": input_screening.to_dict(),
            "message": input_screening.message_to_user,
            "runtime_load": runtime_report.to_dict(),
            "timing_ms": timing.to_dict(),
            "pipeline_stopped": "input_guardrail_block",
        }
        print(json.dumps(payload, indent=2))
        return 0

    tool_report = describe_tool_resolution(runtime, use_test_tools=chat_config.use_test_tools)
    tools = resolve_orchestration_tools(runtime, use_test_tools=chat_config.use_test_tools)
    tool_names = orchestration_tool_names(tools)

    from ai.src.application.chat.routing import skipped_scenario_routing
    from ai.src.domain.chat_system.v1.types import ScenarioAgentInput

    step_started = time.perf_counter()
    if chat_config.enable_scenario_routing:
        routing = await ScenarioAgent().run(
            ScenarioAgentInput(
                agent_id=args.agent_id,
                user_query=user_query,
                message_history=message_history,
            )
        )
    else:
        routing = skipped_scenario_routing()
    timing.record("scenario_routing", step_started)

    scenario_prompt = _scenarios_prompt_for(runtime, routing.scenario_ids)
    primary_scenario_id = routing.scenario_ids[0] if routing.scenario_ids else None
    system_prompt = _build_system_prompt(
        runtime,
        scenario_prompt=scenario_prompt,
        rules=rules,
        knowledge_base_context=None,
        tool_names=tool_names,
        session_conversation_state=SESSION_CONVERSATION_STATE,
    )

    print(
        f"Agent: {runtime.agent_name!r} | "
        f"scenarios={len(runtime.scenarios)} rules={len(runtime.rules)} "
        f"api_tools={len(runtime.api_tools)}\n"
    )
    _print_tool_resolution(tool_report)
    print(f"Routing: scenario_ids={list(routing.scenario_ids)}, kb_id={routing.knowledge_base_id} "
          f"({timing.steps['scenario_routing']:.0f}ms)")
    print(f"Orchestration model: {DEFAULT_CONFIG.provider}/{DEFAULT_CONFIG.model}\n")

    state = build_initial_state(
        agent_id=str(runtime.agent_id),
        version_id=str(runtime.version_id),
        system_prompt=system_prompt,
        user_query=user_query,
        message_history=message_history,
        scenario_id=primary_scenario_id,
        knowledge_base_id=routing.knowledge_base_id,
        conversation_state=SESSION_CONVERSATION_STATE,
    )
    graph = compile_chat_graph(
        DEFAULT_CONFIG,
        tools=tools,
        max_llm_calls=chat_config.max_orchestration_llm_calls,
    )
    step_started = time.perf_counter()
    result = await graph.ainvoke(state)
    timing.record("orchestration", step_started)
    trace = _orchestration_trace(result["messages"])
    if args.verbose:
        _print_orchestration_trace(trace)

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
        enabled=chat_config.enable_output_guardrail,
    )
    timing.record("output_guardrail", step_started)
    _print_output_screening(
        output_screening,
        elapsed_ms=timing.steps.get("output_guardrail"),
    )

    timing.record("total", run_started)

    _print_timing(timing)

    payload = {
        "agent_id": result["agent_id"],
        "version_id": result["version_id"],
        "scenario_ids": list(routing.scenario_ids),
        "scenario_id": primary_scenario_id,
        "knowledge_base_id": result["knowledge_base_id"],
        "llm_calls": result["llm_calls"],
        "message": output_screening.message_to_user,
        "assistant_message_raw": assistant_message,
        "input_guardrail": input_screening.to_dict(),
        "output_guardrail": output_screening.to_dict(),
        "message_history_after_turn": [
            {"role": message.role.value, "content": message.content}
            for message in output_screening.updated_message_history
        ],
        "conversation_state": result["conversation_state"],
        "parse_success": result["parse_success"],
        "message_count": len(result["messages"]),
        "tool_resolution": {
            "source": tool_report.source,
            "deployed_api_tools": list(tool_report.deployed_tools),
            "bound_tools": list(tool_report.bound_tool_names),
        },
        "runtime_load": runtime_report.to_dict(),
        "timing_ms": timing.to_dict(),
        "tool_activity": _tool_calls_summary(result["messages"]),
        "orchestration_trace": trace if args.verbose else None,
    }
    print(json.dumps(payload, indent=2))
    if not output_screening.message_to_user:
        print("\nError: graph finished without a parsed assistant message.")
        return 1
    if output_screening.status in {"block", "reformat", "pass"} and output_screening.message_to_user:
        return 0 if result["parse_success"] or output_screening.status == "reformat" else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
