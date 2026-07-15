"""Ticketing agent smoke test (one combined LLM call on a closed conversation).

Run from repo root:

    python ai/scripts/test_ticketing_agent.py
    python ai/scripts/test_ticketing_agent.py --sentiment
    python ai/scripts/test_ticketing_agent.py --close-reason auto_timeout

Inputs (edit constants below)
-----------------------------
- MESSAGE_HISTORY — the full ended conversation (user/assistant turns)
- SESSION_FACTS — durable facts gathered during the chat (snake_case keys)
- CLOSE_REASON — why the session closed (user_confirmed / transfer_confirmed / auto_timeout)
- ENABLE_SENTIMENT — whether the agent should fill the sentiment field

Requires LLM provider credentials in the environment (same as other AI scripts).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai.src.domain.chat_system.v1.types import (
    TicketingAgentInput,
    TicketingAgentResult,
)
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.infrastructure.chat_system.v1.agents.ticketing_agent import TicketingAgent

# ---------------------------------------------------------------------------
# Edit these
# ---------------------------------------------------------------------------

MESSAGE_HISTORY: tuple[ChatMessage, ...] = (
    ChatMessage(role=MessageRole.USER, content="Hi, my transfer to Nigeria is stuck."),
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content="Sorry to hear that. Can you share the transfer reference?",
    ),
    ChatMessage(role=MessageRole.USER, content="Sure, it's TXN-90871."),
    ChatMessage(
        role=MessageRole.ASSISTANT,
        content=(
            "Thanks. I can see TXN-90871 completed and was delivered to the recipient "
            "a few minutes ago. Anything else I can help with?"
        ),
    ),
    ChatMessage(role=MessageRole.USER, content="Oh great, that's all. Thank you!"),
)

SESSION_FACTS: dict[str, str] = {
    "intent": "transfer_status",
    "transfer_reference": "TXN-90871",
    "destination_country": "Nigeria",
}

CLOSE_REASON = "user_confirmed"
ENABLE_SENTIMENT = False


def _print_result(result: TicketingAgentResult) -> None:
    payload = {
        "worth_ticket": result.worth_ticket,
        "status": result.status,
        "resolution": result.resolution,
        "general_summary": result.general_summary,
        "journey": result.journey,
        "sentiment": result.sentiment,
        "provider": result.provider,
        "model": result.model,
        "parse_success": result.parse_success,
    }
    print(json.dumps(payload, indent=2))
    if not result.parse_success:
        print("\nraw:\n", result.raw)


async def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the post-close ticketing agent.")
    parser.add_argument(
        "--close-reason",
        default=CLOSE_REASON,
        help="Close reason (user_confirmed / transfer_confirmed / auto_timeout).",
    )
    parser.add_argument(
        "--sentiment",
        action="store_true",
        default=ENABLE_SENTIMENT,
        help="Enable sentiment analysis for this run.",
    )
    args = parser.parse_args()

    agent_input = TicketingAgentInput(
        message_history=MESSAGE_HISTORY,
        session_facts=SESSION_FACTS,
        close_reason=args.close_reason,
        enable_sentiment=args.sentiment,
    )

    print(
        f"Analyzing closed conversation: {len(MESSAGE_HISTORY)} turns, "
        f"{len(SESSION_FACTS)} session facts, close_reason={args.close_reason}, "
        f"sentiment={'on' if args.sentiment else 'off'}\n"
    )

    result = await TicketingAgent().run(agent_input)
    _print_result(result)
    return 0 if result.parse_success else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
