"""Unit tests: ai/scripts/eval_prompt_injection.py summary helpers."""
from pathlib import Path

from ai.scripts.eval_prompt_injection import _build_summary, _load_cases

_ROOT = Path(__file__).resolve().parents[4]
_SAMPLE = _ROOT / "data" / "sample" / "prompt_injection.json"


def test_load_cases_reads_prompt_injections() -> None:
    cases = _load_cases(_SAMPLE)

    assert len(cases) == 20
    assert cases[0]["category"] == "ignore_override"


def test_build_summary_calculates_block_rate() -> None:
    results = [
        {"category": "ignore_override", "blocked": True, "passed": True, "parse_success": True},
        {"category": "ignore_override", "blocked": False, "passed": False, "parse_success": True},
        {"category": "exfiltration", "blocked": True, "passed": True, "parse_success": False},
    ]

    summary = _build_summary(results)

    assert summary["total"] == 3
    assert summary["blocked"] == 2
    assert summary["pass_rate"] == round(2 / 3, 4)
    assert summary["all_blocked"] is False
    assert summary["parse_failures"] == 1
    assert summary["by_category"]["ignore_override"]["total"] == 2


def test_load_cases_raises_when_file_has_no_cases(tmp_path) -> None:
    path = tmp_path / "empty.json"
    path.write_text('{"prompt_injections": []}', encoding="utf-8")

    try:
        _load_cases(path)
    except ValueError as exc:
        assert "No prompt_injections" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
