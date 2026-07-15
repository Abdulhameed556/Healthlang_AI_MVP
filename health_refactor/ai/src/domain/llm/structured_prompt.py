"""Build prompts for JSON-in-<json> structured output."""
import json

from ai.src.domain.llm.json_format import JsonOutputFormat

_STRUCTURED_RULES = """\
Output format (MANDATORY): EVERY customer-facing reply MUST be exactly one
<json>...</json> block — and nothing else. This is required for ALL replies with
no exceptions: short answers, long step-by-step answers, greetings, apologies, and
especially when ending the conversation or transferring to a human.
NEVER reply with plain text or markdown outside the <json> tags. Plain-prose replies
are invalid and will be dropped.
No text, markdown fences, or commentary before or after the tags.
Put the customer-facing reply inside the message field using light markdown only:
paragraphs, **bold**, bullet lists (- item), numbered lists (1. item), and [links](url).
The message field must NEVER be empty when you are speaking to the customer — even on
closing or transfer turns, write a complete, helpful closing sentence.
Do not use HTML tags or code fences in message.
Match the structure below; replace dummy values with real data from the source."""


def build_structured_system_prompt(
    base_system_prompt: str,
    output_format: JsonOutputFormat,
    *,
    example: dict | None = None,
) -> str:
    template = output_format.template.strip()
    wrapped = f"<json>\n{template}\n</json>"
    parts = [base_system_prompt.strip(), _STRUCTURED_RULES, "Required shape:", wrapped]
    if example is not None:
        example_json = json.dumps(example, indent=2, ensure_ascii=False)
        parts.append(
            "Example of a complete, valid reply (note BOTH the opening <json> and "
            "closing </json> tags, and the non-empty message):\n"
            f"<json>\n{example_json}\n</json>"
        )
    return "\n\n".join(part for part in parts if part)
