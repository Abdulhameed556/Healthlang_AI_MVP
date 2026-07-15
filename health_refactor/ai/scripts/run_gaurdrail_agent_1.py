"""Quick structured-output smoke test. Run from repo root: python test.py"""
import asyncio
import json

from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.messages import ChatMessage, MessageRole
from ai.src.domain.llm.prompt_templates import ORDER_EXTRACTION_SYSTEM
from ai.src.domain.llm.types import StructuredSingleTaskAgentRequest
from ai.src.infrastructure.llm.factory import get_single_task_provider

# Define output shape inline (dummy values) — same as you'd store on an agent in DB
OUTPUT_FORMAT = JsonOutputFormat.from_example(
    {
        "name": "sam",
        "products": [{"id": "", "title": "", "qty": 0}],
    }
)

USER_MESSAGE = (
    "From: ada@acme.com\n\n"
    "Process for Acme Corp: 1x Widget Pro (id W-100), 2x Gadget Mini (id G-200)."
)

MESSAGE_HISTORY: tuple[ChatMessage, ...] = (
    ChatMessage(role=MessageRole.USER, content="I need to place an order."),
    ChatMessage(role=MessageRole.ASSISTANT, content="Share the line items."),
)


async def main() -> None:
    request = StructuredSingleTaskAgentRequest(
        system_prompt=ORDER_EXTRACTION_SYSTEM,
        prompt=USER_MESSAGE,
        provider="gemini",
        model="gemini-2.5-flash",
        output_format=OUTPUT_FORMAT,
        message_history=MESSAGE_HISTORY,
        temperature=0.1,
        max_tokens=512,
    )

    result = await get_single_task_provider(request.provider).run_structured(request)

    print("parse_success:", result.parse_success)
    print("raw:\n", result.raw)
    print("data:\n", json.dumps(result.data, indent=2))
    if result.parse_errors:
        print("errors:", result.parse_errors)


if __name__ == "__main__":
    asyncio.run(main())
