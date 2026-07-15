"""Unit tests: orchestration in-memory test tools."""
from ai.src.infrastructure.chat_system.v1.orchestration.tools.test_tools import (
    AVAILABLE_DOC_KEYS,
    build_test_tools,
    get_company_doc,
    tools_by_name,
)


def test_get_company_doc_returns_known_policy() -> None:
    text = get_company_doc.invoke({"doc_key": "refund_policy"})

    assert "30 days" in text
    assert "refund" in text.lower()


def test_get_company_doc_lists_available_keys_on_unknown() -> None:
    text = get_company_doc.invoke({"doc_key": "unknown_doc"})

    assert "Unknown doc_key" in text
    for key in AVAILABLE_DOC_KEYS:
        assert key in text


def test_build_test_tools_exposes_get_company_doc() -> None:
    tools = build_test_tools()

    assert len(tools) == 1
    assert tools[0].name == "get_company_doc"


def test_tools_by_name_maps_tool_names() -> None:
    tools = build_test_tools()
    lookup = tools_by_name(tools)

    assert set(lookup) == {"get_company_doc"}
    assert lookup["get_company_doc"] is tools[0]
