"""Unit tests: ai/scripts/test_guardrail_screener.py"""
import argparse

from ai.scripts.test_guardrail_screener import _print_result


def test_main_parser_requires_command() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("input").add_argument("--text", required=True)
    sub.add_parser("output").add_argument("--text", required=True)

    args = parser.parse_args(["input", "--text", "hello"])
    assert args.command == "input"
    assert args.text == "hello"


def test_print_result_builds_payload(monkeypatch, capsys) -> None:
    class _Result:
        blocked = True
        blocked_reason = "bad"
        attack_category = None
        violation_category = None
        provider = "openai"
        model = "gpt-4o-mini"
        parse_success = True

    _print_result(_Result())
    captured = capsys.readouterr()
    assert '"blocked": true' in captured.out
    assert '"provider": "openai"' in captured.out
