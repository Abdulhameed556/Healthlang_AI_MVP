#!/usr/bin/env python3
"""Interactive terminal chat — create a session and talk to the agent.

Run from repo root:

    python chat_terminal.py
    python chat_terminal.py --agent-id <uuid>
    python chat_terminal.py --session-id <uuid>
    python chat_terminal.py --use-session-cache

Type a message and press Enter. Commands:

    /quit, /exit  — end the chat
    /session      — print session id (for resume)
    /state        — print last conversation state
    /help         — show commands
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from uuid import UUID

from ai.src.application.chat.pipeline import ChatPipeline
from ai.src.application.chat.settings import (
    DEFAULT_AGENT_ID,
    add_chat_config_arguments,
    chat_config_from_cli_args,
)
from ai.src.application.chat.types import ChatPipelineInput
from ai.src.domain.chat_system.v1.types import ConversationSessionState
from ai.src.infrastructure.chat_sessions.store import ChatSessionStore
from ai.src.infrastructure.chat_system.v1.agents.scenario_agent.runtime_loader import (
    load_scenario_runtime_with_report,
)

BANNER = """
Afriex support chat (terminal)
------------------------------
"""


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive terminal chat session.")
    parser.add_argument("--agent-id", default=DEFAULT_AGENT_ID, help="Deployed agent UUID.")
    parser.add_argument(
        "--session-id",
        help="Resume an existing chat session instead of creating a new one.",
    )
    add_chat_config_arguments(parser)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full pipeline JSON after each turn.",
    )
    return parser.parse_args()


def _prompt_user() -> str:
    try:
        return input("\nYou: ").strip()
    except (EOFError, KeyboardInterrupt):
        return "/quit"


async def _ensure_session(
    *,
    store: ChatSessionStore,
    args: argparse.Namespace,
    config,
) -> UUID:
    if args.session_id:
        session_id = UUID(args.session_id)
        await store.load(session_id, use_cache=config.use_session_cache)
        print(f"Resumed session: {session_id}")
        return session_id

    runtime, _report = await load_scenario_runtime_with_report(UUID(args.agent_id))
    session = await store.create(
        organization_id=runtime.organization_id,
        agent_id=runtime.agent_id,
        agent_version_id=runtime.version_id,
        use_cache=config.use_session_cache,
    )
    print(f"New session: {session.id}")
    print(f"Agent: {runtime.agent_name!r} (v{runtime.version_number})")
    return session.id


async def _run_turn(
    *,
    pipeline: ChatPipeline,
    session_id: UUID,
    user_message: str,
    config,
    show_json: bool,
) -> tuple[str | None, str]:
    result = await pipeline.run(
        ChatPipelineInput(
            session_id=session_id,
            user_message=user_message,
            config=config,
        )
    )

    session_load = result.turn_metadata.get("session_load", {})
    source = session_load.get("source", "?") if isinstance(session_load, dict) else "?"
    total_ms = result.timing_ms.get("total")
    timing_suffix = f" ({total_ms:.0f}ms, session={source})" if total_ms is not None else ""

    if result.pipeline_stopped:
        print(f"\n[pipeline stopped: {result.pipeline_stopped}]{timing_suffix}")
    else:
        print(timing_suffix)

    if result.message:
        print(f"\nAgent: {result.message}")
    else:
        print("\nAgent: (no message)")

    print(f"State: {result.conversation_state}")

    if show_json:
        print(json.dumps(result.to_dict(), indent=2))

    return result.message, result.conversation_state


async def _chat_loop(args: argparse.Namespace) -> int:
    config = chat_config_from_cli_args(args)
    store = ChatSessionStore()
    pipeline = ChatPipeline(session_store=store)

    print(BANNER)
    print("Commands: /help /session /state /quit")
    print("Resume later: python chat_terminal.py --session-id <id>\n")

    session_id = await _ensure_session(store=store, args=args, config=config)

    last_state = ConversationSessionState.IN_PROGRESS.value

    while True:
        line = await asyncio.to_thread(_prompt_user)

        if not line:
            continue

        lowered = line.lower()
        if lowered in {"/quit", "/exit", "/q"}:
            print(f"\nSession ended. Resume with:\n  python chat_terminal.py --session-id {session_id}")
            return 0

        if lowered == "/help":
            print(__doc__)
            continue

        if lowered == "/session":
            print(f"session_id: {session_id}")
            continue

        if lowered == "/state":
            print(f"conversation_state: {last_state}")
            continue

        _message, last_state = await _run_turn(
            pipeline=pipeline,
            session_id=session_id,
            user_message=line,
            config=config,
            show_json=args.json,
        )

        if last_state == ConversationSessionState.END_CONVERSATION.value:
            print("\n(conversation marked end_conversation — type /quit or send another message)")

    return 0


def main() -> int:
    args = _parse_args()
    try:
        return asyncio.run(_chat_loop(args))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130


if __name__ == "__main__":
    sys.exit(main())
