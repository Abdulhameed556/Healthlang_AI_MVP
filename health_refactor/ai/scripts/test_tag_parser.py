#!/usr/bin/env python3
"""
Step 1 manual test — tag parser only (no API key, no LLM).

From monorepo root:

    python ai/scripts/test_tag_parser.py

    python ai/scripts/test_tag_parser.py --raw '<name>Acme</name>'

    python ai/scripts/test_tag_parser.py \\
      --format-file ai/scripts/fixtures/order_tag_format.xml \\
      --raw-file path/to/model_output.xml
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai.src.domain.llm.tag_format import TagOutputFormat
from ai.src.domain.llm.tag_parser import parse_tag_output

_SAMPLE_RAW = """
<name>Acme Corp</name>
<products>
  <product><id>1</id><title>Widget</title><qty>1</qty></product>
  <product><id>2</id><title>Gadget</title><qty>2</qty></product>
</products>
""".strip()

_FIXTURES = {
    "order": ("ai/scripts/fixtures/order_tag_format.xml", "", _SAMPLE_RAW),
    "ticket": (
        "ai/scripts/fixtures/ticket_tag_format.xml",
        "tag",
        """
<ticket>
  <subject>Cannot login</subject>
  <priority>high</priority>
  <tags>
    <tag>auth</tag>
    <tag>urgent</tag>
  </tags>
</ticket>
""".strip(),
    ),
    "classification": (
        "ai/scripts/fixtures/classification_tag_format.xml",
        "entity",
        """
<intent>refund_request</intent>
<confidence>0.88</confidence>
<entities>
  <entity><type>order_id</type><value>ORD-1</value></entity>
</entities>
""".strip(),
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Test tag output parser (no LLM)")
    parser.add_argument(
        "--format-file",
        default="ai/scripts/fixtures/order_tag_format.xml",
        help="XML tag template file",
    )
    parser.add_argument("--list-tags", default="", help="Comma-separated repeating tags")
    parser.add_argument("--json-tags", default="", help="Comma-separated tags with JSON body")
    parser.add_argument("--raw", default="", help="Raw model output string")
    parser.add_argument("--raw-file", default="", help="File containing raw model output")
    parser.add_argument(
        "--preset",
        choices=sorted(_FIXTURES),
        default="",
        help="Use a built-in format + sample raw (order, ticket, classification)",
    )
    args = parser.parse_args()

    raw = args.raw
    if args.raw_file:
        raw = Path(args.raw_file).read_text(encoding="utf-8")

    if args.preset:
        format_file, list_tags, sample_raw = _FIXTURES[args.preset]
        args.format_file = format_file
        if not args.list_tags:
            args.list_tags = list_tags
        if not raw:
            raw = sample_raw
    elif not raw:
        raw = _SAMPLE_RAW

    template = Path(args.format_file).read_text(encoding="utf-8")

    fmt = TagOutputFormat.from_template(
        template,
        list_tags=args.list_tags,
        json_tags=args.json_tags,
    )
    result = parse_tag_output(raw, fmt)

    print("success:", result.success)
    if result.errors:
        print("errors:", result.errors)
    print(result.to_json())


if __name__ == "__main__":
    main()
