#!/usr/bin/env python3
"""
Parser-only test — no LLM, no API key.

    python ai/scripts/test_json_parser.py --preset order

    python ai/scripts/test_json_parser.py \\
      --format-file ai/scripts/fixtures/order_json_format.json \\
      --raw '<json>{"name":"Acme"}</json>'
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.json_parser import parse_json_output

_SAMPLE_RAW = """<json>
{
  "name": "Acme Corp",
  "products": [
    {"id": "1", "title": "Widget", "qty": 1},
    {"id": "2", "title": "Gadget", "qty": 2}
  ]
}
</json>"""

_FIXTURES = {
    "order": ("ai/scripts/fixtures/order_json_format.json", _SAMPLE_RAW),
    "ticket": (
        "ai/scripts/fixtures/ticket_json_format.json",
        '<json>{"subject":"Login issue","priority":"high","tags":["auth","urgent"]}</json>',
    ),
    "classification": (
        "ai/scripts/fixtures/classification_json_format.json",
        '<json>{"intent":"refund_request","confidence":0.88,'
        '"entities":[{"type":"order_id","value":"ORD-1"}]}</json>',
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Test JSON structured output parser (no LLM)")
    parser.add_argument("--format-file", default="ai/scripts/fixtures/order_json_format.json")
    parser.add_argument("--raw", default="")
    parser.add_argument("--raw-file", default="")
    parser.add_argument("--preset", choices=sorted(_FIXTURES), default="")
    args = parser.parse_args()

    raw = args.raw
    if args.raw_file:
        raw = Path(args.raw_file).read_text(encoding="utf-8")

    if args.preset:
        format_file, sample_raw = _FIXTURES[args.preset]
        args.format_file = format_file
        if not raw:
            raw = sample_raw
    elif not raw:
        raw = _SAMPLE_RAW

    fmt = JsonOutputFormat.from_file(args.format_file)
    result = parse_json_output(raw, fmt)

    print("success:", result.success)
    if result.errors:
        print("errors:", result.errors)
    print(result.to_json())


if __name__ == "__main__":
    main()
