"""Unit tests: ai/scripts/test_image_reader.py"""
import argparse

from ai.scripts.test_image_reader import DEFAULT_IMAGE_URL, _print_result


def test_main_parser_uses_default_url() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_IMAGE_URL)
    parser.add_argument("--caption", default="")
    parser.add_argument("--model", default="")

    args = parser.parse_args([])
    assert args.url == DEFAULT_IMAGE_URL


def test_main_parser_accepts_custom_url() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_IMAGE_URL)
    parser.add_argument("--caption", default="")
    parser.add_argument("--model", default="")

    args = parser.parse_args(["--url", "https://example.com/x.jpg", "--caption", "hi"])
    assert args.url == "https://example.com/x.jpg"
    assert args.caption == "hi"


def test_print_result_includes_enriched_message(capsys) -> None:
    class _Result:
        success = True
        error = None
        description = "A receipt."
        provider = "openai"
        model = "gpt-4o"

    _print_result(_Result(), enriched_message="[Customer attached an image.]")
    captured = capsys.readouterr()
    assert '"success": true' in captured.out
    assert "enriched_user_message" in captured.out
