"""Parse <json>...</json> LLM output into dicts."""
import json
import re
from dataclasses import dataclass
from typing import Any

from ai.src.domain.llm.json_format import JsonOutputFormat

_JSON_TAG_RE = re.compile(r"<json>\s*(.*?)\s*</json>", re.DOTALL | re.IGNORECASE)
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
_TAG_TOKEN_RE = re.compile(r"</?json>", re.IGNORECASE)


@dataclass(frozen=True)
class JsonParseResult:
    data: dict[str, Any]
    raw: str
    success: bool
    errors: list[str]

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.data, indent=indent)


def _normalize_raw_output(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = _FENCE_RE.sub("", stripped).strip()
    return stripped


def _extract_json_text(raw: str) -> str:
    cleaned = _normalize_raw_output(raw)
    if not cleaned:
        return ""

    match = _JSON_TAG_RE.search(cleaned)
    if match:
        return match.group(1).strip()

    # Tolerate malformed wrappers so a well-formed JSON body never leaks raw:
    # a lone/opening <json> with no closing tag, a closing tag only, or prose
    # around the JSON. Strip stray tags, then fall back to the first '{'..last '}'.
    without_tags = _TAG_TOKEN_RE.sub(" ", cleaned).strip()
    if without_tags.startswith("{"):
        return without_tags

    start = without_tags.find("{")
    end = without_tags.rfind("}")
    if start != -1 and end != -1 and end > start:
        return without_tags[start : end + 1]

    return without_tags


def parse_json_output(raw: str, fmt: JsonOutputFormat) -> JsonParseResult:
    """Extract JSON from model output and parse to a dict."""
    errors: list[str] = []
    json_text = _extract_json_text(raw)

    if not json_text:
        return JsonParseResult(
            data={},
            raw=raw,
            success=False,
            errors=["Empty model output"],
        )

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        return JsonParseResult(
            data={},
            raw=raw,
            success=False,
            errors=[f"JSON parse error: {exc}"],
        )

    if not isinstance(data, dict):
        return JsonParseResult(
            data={},
            raw=raw,
            success=False,
            errors=["Root JSON must be an object"],
        )

    if not data:
        errors.append("Empty JSON object")

    return JsonParseResult(
        data=data,
        raw=raw,
        success=bool(data) and not errors,
        errors=errors,
    )
