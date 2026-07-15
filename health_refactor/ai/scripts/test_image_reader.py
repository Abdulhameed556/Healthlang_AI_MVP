#!/usr/bin/env python3
"""
Manual test for the image reader agent.

Run from monorepo root:

    python ai/scripts/test_image_reader.py
    python ai/scripts/test_image_reader.py --url "https://example.com/image.jpg"
    python ai/scripts/test_image_reader.py --caption "My transfer failed"

Requires OPENAI_API_KEY in .env.
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

from ai.src.application.chat.image_context import build_user_message_with_image_context
from ai.src.domain.chat_system.v1.types import AgentLLMConfig, ImageReaderAgentInput
from ai.src.infrastructure.chat_system.v1.agents.image_reader import ImageReaderAgent

DEFAULT_IMAGE_URL = (
    "https://fc-use1-00-pics-bkt-00.s3.amazonaws.com/a043f09ca54f6c11636008c5dd129d096"
    "a1a2da46248e07fd1f4509ea53eb3f5/f_feedbackMessage/u_e8d778a6e3d80ce3bca3485c176"
    "ab919e3dbff0c896585a3d1892eb05ac25bad/img_i7k5t9sf46_d27a0a6ea6a44302c7d9ecced"
    "750951d54a69095e571eef65b385bef652627e6.jpg"
)


def _print_result(result, *, enriched_message: str | None = None) -> None:
    payload = {
        "success": result.success,
        "error": result.error,
        "description": result.description,
        "provider": result.provider,
        "model": result.model,
    }
    if enriched_message is not None:
        payload["enriched_user_message"] = enriched_message
    print(json.dumps(payload, indent=2, default=str))


async def _cmd_read(args: argparse.Namespace) -> int:
    config = None
    if args.model:
        config = AgentLLMConfig(
            provider="openai",
            model=args.model,
            prompt_version="v1",
            temperature=0.0,
            max_tokens=1024,
        )

    agent = ImageReaderAgent(config=config)
    result = await agent.run(
        ImageReaderAgentInput(
            image_urls=(args.url,),
            caption=args.caption or "",
        )
    )

    enriched = None
    if result.success:
        enriched = build_user_message_with_image_context(
            caption=args.caption or "",
            image_description=result.description,
        )
    _print_result(result, enriched_message=enriched)
    return 0 if result.success else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Test the image reader agent.")
    parser.add_argument(
        "--url",
        default=DEFAULT_IMAGE_URL,
        help="Public image URL (default: Freshchat sample attachment)",
    )
    parser.add_argument(
        "--caption",
        default="",
        help="Optional customer text sent with the image",
    )
    parser.add_argument(
        "--model",
        default="",
        help="Override vision model (default: gpt-4o from agent config)",
    )
    args = parser.parse_args()
    return asyncio.run(_cmd_read(args))


if __name__ == "__main__":
    raise SystemExit(main())
