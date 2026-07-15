#!/usr/bin/env python3
"""
Manual tests for single-task LLM providers: run, stream, structured.

Requires OPENAI_API_KEY in .env. Run from monorepo root:

    python ai/scripts/test_single_task_agent.py list-providers

    python ai/scripts/test_single_task_agent.py run
    python ai/scripts/test_single_task_agent.py run --prompt "Say hi in 3 words."

    python ai/scripts/test_single_task_agent.py stream

    python ai/scripts/test_single_task_agent.py structured --preset order
    python ai/scripts/test_single_task_agent.py structured --preset order --dry-run
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai.scripts.llm_presets import STRUCTURED_PRESETS
from ai.src.application.single_task_agent import SingleTaskAgentRunner
from ai.src.domain.llm.json_format import JsonOutputFormat
from ai.src.domain.llm.structured_prompt import build_structured_system_prompt
from ai.src.domain.llm.types import SingleTaskAgentRequest, StructuredSingleTaskAgentRequest
from ai.src.infrastructure.llm.factory import get_single_task_provider, list_single_task_providers


def _add_provider_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--provider", default="openai")
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--max-tokens", type=int, default=512)
    parser.add_argument("--max-retries", type=int, default=2)


def _section(title: str, body: str) -> None:
    print(f"\n{'=' * 60}")
    print(title)
    print("=" * 60)
    print(body)


async def _cmd_list_providers(_args: argparse.Namespace) -> int:
    print("Registered providers:", ", ".join(list_single_task_providers()))
    return 0


async def _cmd_run(args: argparse.Namespace) -> int:
    request = SingleTaskAgentRequest(
        system_prompt=args.system,
        prompt=args.prompt,
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        max_retries=args.max_retries,
        stream=False,
    )
    result = await SingleTaskAgentRunner().run(request)
    print("content:", result.content)
    if result.usage:
        print(
            "usage:",
            f"in={result.usage.input_tokens}",
            f"out={result.usage.output_tokens}",
            f"total={result.usage.total_tokens}",
        )
    return 0


async def _cmd_stream(args: argparse.Namespace) -> int:
    request = SingleTaskAgentRequest(
        system_prompt=args.system,
        prompt=args.prompt,
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        max_retries=args.max_retries,
        stream=True,
        stream_usage=args.stream_usage,
    )
    print("--- stream ---")
    async for token in SingleTaskAgentRunner().stream(request):
        print(token, end="", flush=True)
    print("\n--- end ---")
    return 0


async def _cmd_structured(args: argparse.Namespace) -> int:
    preset = STRUCTURED_PRESETS.get(args.preset) if args.preset else None
    format_file = args.format_file or (preset.format_file if preset else "")
    if not format_file:
        print("Error: pass --preset or --format-file", file=sys.stderr)
        return 1

    system = args.system if args.system is not None else (preset.system if preset else "")
    prompt = args.prompt if args.prompt is not None else (preset.prompt if preset else "")
    if not system or not prompt:
        print("Error: --system and --prompt required (or use --preset)", file=sys.stderr)
        return 1

    output_format = JsonOutputFormat.from_file(format_file)
    built_system = build_structured_system_prompt(system, output_format)

    _section("PROVIDER", f"{args.provider} / {args.model}")
    _section("JSON FORMAT", output_format.template)
    _section("SYSTEM PROMPT", built_system)
    _section("USER PROMPT", prompt)

    if args.dry_run:
        print("\n(dry-run: no LLM call)")
        return 0

    request = StructuredSingleTaskAgentRequest(
        system_prompt=system,
        prompt=prompt,
        provider=args.provider,
        model=args.model,
        output_format=output_format,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        max_retries=args.max_retries,
    )

    print("\nCalling provider.run_structured()...")
    provider = get_single_task_provider(args.provider)
    result = await provider.run_structured(request)

    _section("RAW OUTPUT", result.raw)
    _section("PARSED JSON", json.dumps(result.data, indent=2) if result.data else "(empty)")
    if result.usage:
        _section(
            "TOKEN USAGE",
            f"input={result.usage.input_tokens} "
            f"output={result.usage.output_tokens} "
            f"total={result.usage.total_tokens}",
        )

    print(f"\nparse_success: {result.parse_success}")
    if result.parse_errors:
        print("parse_errors:", result.parse_errors)
        return 1
    return 0


def _cmd_list_presets(_args: argparse.Namespace) -> int:
    print("Structured presets:")
    for name, preset in STRUCTURED_PRESETS.items():
        print(f"  {name}")
        print(f"    format: {preset.format_file}")
        print(f"    prompt: {preset.prompt[:70]}...")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Test single-task LLM providers")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-providers", help="Show registered providers")
    sub.add_parser("list-presets", help="Show structured extraction presets")

    run_p = sub.add_parser("run", help="One-shot completion")
    _add_provider_args(run_p)
    run_p.add_argument("--system", default="You are a concise assistant.")
    run_p.add_argument("--prompt", default="Say hello in one short sentence.")

    stream_p = sub.add_parser("stream", help="Stream completion tokens")
    _add_provider_args(stream_p)
    stream_p.add_argument("--stream-usage", action="store_true")
    stream_p.add_argument("--system", default="You are a concise assistant.")
    stream_p.add_argument("--prompt", default="Count from 1 to 5 slowly.")

    struct_p = sub.add_parser("structured", help="JSON shape → <json> output via run_structured")
    _add_provider_args(struct_p)
    struct_p.add_argument("--preset", choices=sorted(STRUCTURED_PRESETS), default="order")
    struct_p.add_argument("--format-file", default="", help="JSON example file (dummy values)")
    struct_p.add_argument("--system", default=None)
    struct_p.add_argument("--prompt", default=None)
    struct_p.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.command == "list-presets":
        raise SystemExit(_cmd_list_presets(args))

    exit_code = asyncio.run(
        {
            "list-providers": _cmd_list_providers,
            "run": _cmd_run,
            "stream": _cmd_stream,
            "structured": _cmd_structured,
        }[args.command](args)
    )
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
