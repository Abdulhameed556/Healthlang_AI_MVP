"""Unit tests: ai/src/domain/llm/structured_prompt.py"""
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.structured_prompt import build_structured_system_prompt


def test_build_structured_system_prompt_includes_rules_and_json_shape() -> None:
    fmt = JsonOutputFormat.from_example({"name": "sam", "items": [{"id": ""}]})

    prompt = build_structured_system_prompt("You are helpful.", fmt)

    assert "You are helpful." in prompt
    assert "<json>" in prompt
    assert '"name": "sam"' in prompt
    assert "Required shape:" in prompt
    assert "exactly one\n<json>" in prompt
    assert "light markdown only" in prompt
    assert "Do not use HTML tags or code fences in message" in prompt


def test_build_structured_system_prompt_omits_example_by_default() -> None:
    fmt = JsonOutputFormat.from_example({"name": "sam"})

    prompt = build_structured_system_prompt("You are helpful.", fmt)

    assert "Example of a complete, valid reply" not in prompt


def test_build_structured_system_prompt_includes_one_shot_example() -> None:
    fmt = JsonOutputFormat.from_example({"name": "sam"})

    prompt = build_structured_system_prompt(
        "You are helpful.",
        fmt,
        example={"name": "Acme", "items": []},
    )

    assert "Example of a complete, valid reply" in prompt
    assert '"name": "Acme"' in prompt
    assert prompt.count("</json>") >= 2
