"""Unit tests: ai/src/domain/llm/json_parser.py"""
import json

from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.json_parser import parse_json_output

_FMT = JsonOutputFormat.from_example({"name": "sam", "products": [{"id": "", "qty": 0}]})


def _parse(raw: str, fmt: JsonOutputFormat = _FMT) -> dict:
    return parse_json_output(raw, fmt).data


def test_parse_json_tag_wrapper() -> None:
    raw = '<json>{"name": "Acme", "products": [{"id": "1", "qty": 2}]}</json>'
    data = _parse(raw)
    assert data["name"] == "Acme"
    assert data["products"][0]["id"] == "1"


def test_parse_bare_json_object() -> None:
    raw = '{"name": "Acme", "products": []}'
    data = _parse(raw)
    assert data["name"] == "Acme"


def test_parse_strips_markdown_fence() -> None:
    raw = '```json\n{"name": "Acme", "products": []}\n```'
    result = parse_json_output(raw, _FMT)
    assert result.success is True
    assert result.data["name"] == "Acme"


def test_parse_multiline_json_inside_tag() -> None:
    raw = """<json>
{
  "name": "Acme Corp",
  "products": [
    {"id": "W-100", "title": "Widget", "qty": 1},
    {"id": "G-200", "title": "Gadget", "qty": 2}
  ]
}
</json>"""
    fmt = JsonOutputFormat.from_file("ai/scripts/fixtures/order_json_format.json")
    result = parse_json_output(raw, fmt)
    assert result.success is True
    assert result.data["name"] == "Acme Corp"
    assert len(result.data["products"]) == 2
    assert result.data["products"][1]["qty"] == 2


def test_parse_ticket_format() -> None:
    raw = '<json>{"subject":"Login","priority":"high","tags":["auth"]}</json>'
    fmt = JsonOutputFormat.from_file("ai/scripts/fixtures/ticket_json_format.json")
    data = _parse(raw, fmt)
    assert data["priority"] == "high"
    assert data["tags"] == ["auth"]


def test_parse_recovers_when_closing_tag_missing() -> None:
    raw = '<json>\n{"name": "Acme", "products": []}'
    data = _parse(raw)
    assert data["name"] == "Acme"


def test_parse_recovers_with_only_closing_tag() -> None:
    raw = '{"name": "Acme", "products": []}\n</json>'
    data = _parse(raw)
    assert data["name"] == "Acme"


def test_parse_recovers_from_prose_around_json() -> None:
    raw = 'Sure, here you go:\n{"name": "Acme", "products": []}\nLet me know!'
    data = _parse(raw)
    assert data["name"] == "Acme"


def test_parse_invalid_json_fails() -> None:
    result = parse_json_output("<json>{bad json}</json>", _FMT)
    assert result.success is False
    assert result.errors


def test_parse_empty_output_fails() -> None:
    result = parse_json_output("   ", _FMT)
    assert result.success is False


def test_parse_root_array_fails() -> None:
    result = parse_json_output("<json>[1, 2]</json>", _FMT)
    assert result.success is False
    assert "object" in result.errors[0].lower()


def test_json_format_from_example_dict() -> None:
    fmt = JsonOutputFormat.from_example({"name": "sam"})
    assert json.loads(fmt.template) == {"name": "sam"}
