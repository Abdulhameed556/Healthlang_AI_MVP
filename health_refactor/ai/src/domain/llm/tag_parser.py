"""Parse tag-based LLM output into JSON-compatible dicts."""
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Any

from ai.src.domain.llm.tag_format import TagOutputFormat

_FENCE_RE = re.compile(r"^```(?:xml)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
_XML_DECL_RE = re.compile(r"<\?xml[^?]*\?\>", re.IGNORECASE)


@dataclass(frozen=True)
class TagParseResult:
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
    stripped = _XML_DECL_RE.sub("", stripped).strip()
    return stripped


def _element_to_value(
    element: ET.Element,
    *,
    list_tags: frozenset[str],
    json_tags: frozenset[str],
) -> Any:
    children = list(element)
    if not children:
        text = (element.text or "").strip()
        if element.tag in json_tags and text:
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return text

    grouped: dict[str, list[ET.Element]] = {}
    for child in children:
        grouped.setdefault(child.tag, []).append(child)

    result: dict[str, Any] = {}
    for tag, elements in grouped.items():
        values = [
            _element_to_value(el, list_tags=list_tags, json_tags=json_tags)
            for el in elements
        ]
        if tag in list_tags or len(elements) > 1:
            result[tag] = values
        else:
            result[tag] = values[0]
    return result


def _merge_root_child(data: dict[str, Any], tag: str, value: Any) -> None:
    if tag not in data:
        data[tag] = value
        return
    existing = data[tag]
    if isinstance(existing, list):
        existing.append(value)
    else:
        data[tag] = [existing, value]


def parse_tag_output(raw: str, fmt: TagOutputFormat) -> TagParseResult:
    """Convert model tag output to a dict using ``fmt`` list/json tag rules."""
    errors: list[str] = []
    cleaned = _normalize_raw_output(raw)
    if not cleaned:
        return TagParseResult(
            data={},
            raw=raw,
            success=False,
            errors=["Empty model output"],
        )

    wrapper = f"<root>{cleaned}</root>"
    try:
        root = ET.fromstring(wrapper)
    except ET.ParseError as exc:
        return TagParseResult(
            data={},
            raw=raw,
            success=False,
            errors=[f"XML parse error: {exc}"],
        )

    data: dict[str, Any] = {}
    for child in root:
        value = _element_to_value(
            child,
            list_tags=fmt.list_tags,
            json_tags=fmt.json_tags,
        )
        if child.tag in fmt.list_tags and not isinstance(value, list):
            value = [value]
        _merge_root_child(data, child.tag, value)

    if not data:
        errors.append("No top-level tags found in output")

    return TagParseResult(
        data=data,
        raw=raw,
        success=bool(data) and not errors,
        errors=errors,
    )
