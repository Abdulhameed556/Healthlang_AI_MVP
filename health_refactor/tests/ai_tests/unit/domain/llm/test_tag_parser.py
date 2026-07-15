"""Unit tests: ai/src/domain/llm/tag_parser.py — many output shapes → JSON."""
import json

import pytest

from ai.src.domain.llm.tag_format import TagOutputFormat
from ai.src.domain.llm.tag_parser import parse_tag_output


def _parse(
    raw: str,
    *,
    template: str = "<root></root>",
    list_tags: str = "",
    json_tags: str = "",
) -> dict:
    fmt = TagOutputFormat.from_template(
        template,
        list_tags=list_tags,
        json_tags=json_tags,
    )
    result = parse_tag_output(raw, fmt)
    assert result.success, result.errors
    return result.data


# ── Flat & simple ──────────────────────────────────────────────────────────


def test_flat_string_fields() -> None:
    data = _parse(
        "<name>Acme Corp</name><score>42</score>",
        template="<name></name><score></score>",
    )
    assert data == {"name": "Acme Corp", "score": "42"}


def test_empty_leaf_tags() -> None:
    data = _parse(
        "<name></name><note></note>",
        template="<name></name><note></note>",
    )
    assert data == {"name": "", "note": ""}


def test_whitespace_in_text_is_trimmed() -> None:
    data = _parse(
        "<summary>  hello world  </summary>",
        template="<summary></summary>",
    )
    assert data == {"summary": "hello world"}


# ── Nesting ────────────────────────────────────────────────────────────────


def test_nested_object_address() -> None:
    raw = """
<customer>
  <name>Ada</name>
  <address>
    <city>Lagos</city>
    <country>NG</country>
  </address>
</customer>
""".strip()
    data = _parse(raw, template="<customer><name></name><address></address></customer>")
    assert data == {
        "customer": {
            "name": "Ada",
            "address": {"city": "Lagos", "country": "NG"},
        }
    }


def test_deep_three_level_nesting() -> None:
    raw = """
<org>
  <team>
    <member>
      <name>Sam</name>
      <role>admin</role>
    </member>
  </team>
</org>
""".strip()
    data = _parse(raw, template="<org><team><member></member></team></org>")
    assert data["org"]["team"]["member"] == {"name": "Sam", "role": "admin"}


# ── Lists ──────────────────────────────────────────────────────────────────


def test_repeated_siblings_auto_list_without_list_tags() -> None:
    raw = "<tag>red</tag><tag>blue</tag><tag>green</tag>"
    data = _parse(raw, template="<tag></tag>")
    assert data == {"tag": ["red", "blue", "green"]}


def test_list_tags_single_item_still_array() -> None:
    raw = "<item><id>1</id></item>"
    data = _parse(raw, template="<item><id></id></item>", list_tags="item")
    assert data == {"item": [{"id": "1"}]}


def test_order_products_nested_list() -> None:
    raw = """
<name>Acme</name>
<products>
  <product><id>1</id><title>Widget</title><qty>1</qty></product>
  <product><id>2</id><title>Gadget</title><qty>2</qty></product>
</products>
""".strip()
    template = (
        "<name></name><products><product><id></id><title></title>"
        "<qty></qty></product></products>"
    )
    data = _parse(raw, template=template)
    assert data["name"] == "Acme"
    assert data["products"]["product"] == [
        {"id": "1", "title": "Widget", "qty": "1"},
        {"id": "2", "title": "Gadget", "qty": "2"},
    ]


def test_order_qty_avoids_duplicate_product_rows() -> None:
    raw = """
<name>Acme</name>
<products>
  <product><id>G-200</id><title>Gadget Mini</title><qty>2</qty></product>
</products>
""".strip()
    template = (
        "<name></name><products><product><id></id><title></title>"
        "<qty></qty></product></products>"
    )
    data = _parse(raw, template=template, list_tags="product")
    assert data["products"]["product"] == [
        {"id": "G-200", "title": "Gadget Mini", "qty": "2"},
    ]


def test_duplicate_root_tags_merge_to_list() -> None:
    raw = "<line>first</line><line>second</line>"
    data = _parse(raw, template="<line></line>")
    assert data == {"line": ["first", "second"]}


# ── Domain-shaped examples (any format via tags) ───────────────────────────


def test_support_ticket_format() -> None:
    raw = """
<ticket>
  <subject>Login issue</subject>
  <priority>high</priority>
  <tags>
    <tag>auth</tag>
    <tag>urgent</tag>
  </tags>
</ticket>
""".strip()
    data = _parse(
        raw,
        template="<ticket><subject></subject><priority></priority><tags><tag></tag></tags></ticket>",
        list_tags="tag",
    )
    assert data["ticket"]["subject"] == "Login issue"
    assert data["ticket"]["priority"] == "high"
    assert data["ticket"]["tags"]["tag"] == ["auth", "urgent"]


def test_classification_format() -> None:
    raw = """
<intent>refund_request</intent>
<confidence>0.92</confidence>
<entities>
  <entity>
    <type>order_id</type>
    <value>ORD-99</value>
  </entity>
  <entity>
    <type>amount</type>
    <value>49.99</value>
  </entity>
</entities>
""".strip()
    data = _parse(
        raw,
        template="<intent></intent><confidence></confidence><entities><entity></entity></entities>",
        list_tags="entity",
    )
    assert data["intent"] == "refund_request"
    assert data["confidence"] == "0.92"
    assert data["entities"]["entity"] == [
        {"type": "order_id", "value": "ORD-99"},
        {"type": "amount", "value": "49.99"},
    ]


def test_user_profile_with_json_tag() -> None:
    raw = '<metadata>{"plan": "pro", "seats": 5}</metadata><email>a@b.com</email>'
    data = _parse(
        raw,
        template="<metadata></metadata><email></email>",
        json_tags="metadata",
    )
    assert data["email"] == "a@b.com"
    assert data["metadata"] == {"plan": "pro", "seats": 5}


def test_json_tag_invalid_falls_back_to_string() -> None:
    raw = "<payload>not-json</payload>"
    data = _parse(raw, template="<payload></payload>", json_tags="payload")
    assert data == {"payload": "not-json"}


def test_json_array_inside_tag() -> None:
    raw = '<ids>["a","b","c"]</ids>'
    data = _parse(raw, template="<ids></ids>", json_tags="ids")
    assert data == {"ids": ["a", "b", "c"]}


# ── Wrapping / cleanup ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw",
    [
        "<name>Fenced</name>",
        "```xml\n<name>Fenced</name>\n```",
        "```\n<name>Fenced</name>\n```",
        '<?xml version="1.0"?><name>Fenced</name>',
    ],
)
def test_normalizes_common_llm_wrappers(raw: str) -> None:
    data = _parse(raw, template="<name></name>")
    assert data == {"name": "Fenced"}


def test_to_json_helper() -> None:
    result = parse_tag_output(
        "<name>Acme</name>",
        TagOutputFormat(template="<name></name>"),
    )
    assert json.loads(result.to_json()) == {"name": "Acme"}


# ── Failures ───────────────────────────────────────────────────────────────


def test_invalid_xml_fails() -> None:
    result = parse_tag_output("<name>unclosed", TagOutputFormat(template="<name></name>"))
    assert result.success is False
    assert result.data == {}
    assert result.errors


def test_empty_output_fails() -> None:
    result = parse_tag_output("   ", TagOutputFormat(template="<name></name>"))
    assert result.success is False
    assert "Empty" in result.errors[0]


def test_xml_special_chars_must_be_escaped() -> None:
    """Ampersand in text must be &amp; per XML rules."""
    result = parse_tag_output(
        "<note>Tom & Jerry</note>",
        TagOutputFormat(template="<note></note>"),
    )
    assert result.success is False
