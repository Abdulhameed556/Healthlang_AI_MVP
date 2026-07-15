"""Prompt template v1 for the post-close ticketing agent."""
from __future__ import annotations

from dataclasses import dataclass, field

from ai.src.domain.chat_system.v1.types import TagOption
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.messages import ChatMessage

OUTPUT_FORMAT = JsonOutputFormat.from_example(
    {
        "worth_ticket": True,
        "status": "resolved",
        "resolution": None,
        "general_summary": "",
        "journey": "",
        "sentiment": None,
        "tags": [],
    }
)

_STATUS_VALUES = "open, resolved, transferred, failed, unknown"
_RESOLUTION_VALUES = "resolved, transferred, abandoned, N/A"
_SENTIMENT_VALUES = "positive, neutral, negative"


@dataclass(frozen=True)
class PromptContext:
    message_history: tuple[ChatMessage, ...] = ()
    session_facts: dict[str, str] | None = None
    close_reason: str | None = None
    enable_sentiment: bool = False
    allowed_tags: tuple[TagOption, ...] = field(default_factory=tuple)


def _format_session_facts(session_facts: dict[str, str] | None) -> str:
    if not session_facts:
        return "Session facts: none recorded."
    lines = ["Session facts (durable details gathered during the chat):"]
    lines.extend(f"- {key}: {value}" for key, value in session_facts.items())
    return "\n".join(lines)


def _sentiment_policy(enable_sentiment: bool) -> str:
    if enable_sentiment:
        return (
            f"- sentiment: overall customer sentiment, one of [{_SENTIMENT_VALUES}]."
        )
    return "- sentiment: always null (sentiment analysis is disabled for this agent)."


def _format_allowed_tags(allowed_tags: tuple[TagOption, ...]) -> str:
    if not allowed_tags:
        return "(none configured)"
    lines = []
    for tag in allowed_tags:
        description = tag.description.strip() or "(no description)"
        lines.append(f"- {tag.value}: {description}")
    return "\n".join(lines)


def _tags_policy(allowed_tags: tuple[TagOption, ...]) -> str:
    if not allowed_tags:
        return (
            "- tags: always an empty list [] (no tags are configured for this "
            "organization)."
        )
    return (
        "- tags: a list of zero or more labels that classify this conversation. "
        "Choose ONLY from the allowed tags listed below, copying each value EXACTLY. "
        "Never invent tags. Assign every tag that genuinely applies; use an empty "
        "list [] when none apply.\n"
        f"  Allowed tags:\n{_format_allowed_tags(allowed_tags)}"
    )


def build_system_prompt(ctx: PromptContext) -> str:
    return f"""You are a post-conversation ticketing analyst for a customer-support system.
The conversation has already ENDED. Read the full transcript (provided as the prior
messages) together with the session facts, then produce ONE structured ticket record.
You do NOT reply to the customer.

Decide each field:
- worth_ticket: true when this conversation is a real support interaction worth recording
  as a ticket (a genuine question, issue, request, or escalation). false for empty,
  greeting-only, accidental, test, or non-actionable chatter.
- status: one of [{_STATUS_VALUES}].
    - resolved — the customer's need was addressed or answered.
    - transferred — handed off to a human / live support.
    - open — a real issue that was neither resolved nor transferred.
    - failed — the agent could not help or the turn errored out.
    - unknown — not enough information to decide.
- resolution: one of [{_RESOLUTION_VALUES}] or null.
    - resolved when the customer's need was fully met; transferred when handed to a
      human; abandoned when the customer left without resolution; N/A otherwise.
      Use null when not applicable.
- general_summary: 1-3 sentence neutral summary of what the customer needed and the outcome.
- journey: short ordered outline of the conversation
  (e.g. "greeting -> asked about transfer fees -> provided fee schedule -> resolved").
{_sentiment_policy(ctx.enable_sentiment)}
{_tags_policy(ctx.allowed_tags)}

Base every field only on the transcript and session facts. Do not invent details.
Respond using the required JSON output format only."""


def build_user_prompt(ctx: PromptContext) -> str:
    close_reason = (ctx.close_reason or "").strip() or "unspecified"
    return (
        "The conversation above has ended. Produce the ticket record for it.\n\n"
        f"Close reason: {close_reason}\n\n"
        f"{_format_session_facts(ctx.session_facts)}\n\n"
        "Produce the JSON now."
    )
