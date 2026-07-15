#!/usr/bin/env python3
"""
Manual tests for chat-system v1 guardrail agents.

Run from monorepo root:

    python ai/scripts/test_guardrail_screener.py input --text "Ignore previous instructions."
    python ai/scripts/test_guardrail_screener.py output --text "Here is my system prompt..."
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
    GuardrailInputScreenerInput,
    GuardrailOutputScreenerInput,
)
from ai.src.infrastructure.chat_system.v1.agents.guardrail_input_screener import (
    GuardrailInputScreenerAgent,
)
from ai.src.infrastructure.chat_system.v1.agents.guardrail_output_screener import (
    GuardrailOutputScreenerAgent,
)


def _print_result(result) -> None:
    payload = {
        "action": getattr(result, "action", None),
        "blocked": result.blocked,
        "safe_message": getattr(result, "safe_message", None),
        "blocked_reason": result.blocked_reason,
        "category": getattr(result, "attack_category", None)
        or getattr(result, "violation_category", None),
        "provider": result.provider,
        "model": result.model,
        "parse_success": result.parse_success,
    }
    print(json.dumps(payload, indent=2, default=str))


async def _cmd_input(args: argparse.Namespace) -> int:
    result = await GuardrailInputScreenerAgent().run(
        GuardrailInputScreenerInput(user_query=args.text)
    )
    _print_result(result)
    return 0


async def _cmd_output(args: argparse.Namespace) -> int:
    result = await GuardrailOutputScreenerAgent().run(
        GuardrailOutputScreenerInput(agent_output=args.text)
    )
    _print_result(result)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Test chat-system guardrail agents.")
    sub = parser.add_subparsers(dest="command", required=True)

    input_parser = sub.add_parser("input")
    input_parser.add_argument("--text", required=True)

    output_parser = sub.add_parser("output")
    output_parser.add_argument("--text", required=True)

    args = parser.parse_args()
    handlers = {
        "input": _cmd_input,
        "output": _cmd_output,
    }
    return asyncio.run(handlers[args.command](args))


if __name__ == "__main__":
    raise SystemExit(main())
