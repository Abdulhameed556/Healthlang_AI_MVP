"""Unit tests: ai/src/application/single_task_agent/prompt_builder.py"""


def test_prompt_builder_re_exports_build_structured_system_prompt() -> None:
    from ai.src.application.single_task_agent.prompt_builder import (
        build_structured_system_prompt,
    )

    assert callable(build_structured_system_prompt)
