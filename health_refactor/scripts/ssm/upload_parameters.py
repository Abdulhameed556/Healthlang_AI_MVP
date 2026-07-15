#!/usr/bin/env python3
"""Bulk-upload SSM Parameter Store values from a JSON file.

Usage:
  cp scripts/ssm/supportos-prod.parameters.example.json scripts/ssm/supportos-prod.parameters.json
  # edit supportos-prod.parameters.json with real secrets
  python scripts/ssm/upload_parameters.py --file scripts/ssm/supportos-prod.parameters.json

Keys become /supportos/prod/<KEY> by default (see --prefix).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SECURE_KEYS = frozenset(
    {
        "DATABASE_URL",
        "REDIS_URL",
        "DRAMATIQ_BROKER_URL",
        "VECTOR_STORE_URL",
        "JWT_SECRET_KEY",
        "ADMIN_JWT_SECRET_KEY",
        "API_TOOL_SECRETS_ENCRYPTION_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "MAILGUN_API_KEY",
        "SMTP_PASSWORD",
        "GOOGLE_CLIENT_SECRET",
        "AI_SERVICE_INTERNAL_API_KEY",
        "ADMIN_INTERNAL_API_KEY",
        "BACKEND_INTERNAL_API_KEY",
        "INTERNAL_API_KEY",
        "FRESHCHAT_WEBHOOK_PUBLIC_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GROQ_API_KEY",
        "GOOGLE_API_KEY",
        "PINECONE_API_KEY",
    }
)

SECURE_SUFFIXES = ("_KEY", "_SECRET", "_PASSWORD", "_URL")


def is_secure(name: str) -> bool:
    if name in SECURE_KEYS:
        return True
    return any(name.endswith(suffix) for suffix in SECURE_SUFFIXES)


def load_parameters(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected a JSON object at the top level")
    out: dict[str, str] = {}
    for key, value in data.items():
        if key.startswith("_"):
            continue
        if value is None:
            value = ""
        if not isinstance(value, str):
            raise SystemExit(f"{path}: value for {key!r} must be a string")
        out[key] = value
    return out


def put_parameter(
    *,
    region: str,
    name: str,
    value: str,
    param_type: str,
    dry_run: bool,
) -> None:
    cmd = [
        "aws",
        "ssm",
        "put-parameter",
        "--region",
        region,
        "--name",
        name,
        "--type",
        param_type,
        "--value",
        value,
        "--overwrite",
    ]
    if dry_run:
        print(f"[dry-run] {name} ({param_type})")
        return
    subprocess.run(cmd, check=True)
    print(f"ok {name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        type=Path,
        required=True,
        help="JSON file with env var names as keys",
    )
    parser.add_argument(
        "--prefix",
        default="/supportos/prod",
        help="SSM path prefix (default: /supportos/prod)",
    )
    parser.add_argument("--region", default="us-east-1")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without calling AWS",
    )
    parser.add_argument(
        "--skip-empty",
        action="store_true",
        help="Skip keys whose value is empty string",
    )
    parser.add_argument(
        "--empty-placeholder",
        default="-",
        help="Value to store when a key is empty (SSM rejects zero-length; default: '-')",
    )
    args = parser.parse_args()

    if not args.file.is_file():
        raise SystemExit(f"File not found: {args.file}")

    parameters = load_parameters(args.file)
    if not parameters:
        raise SystemExit(f"No parameters found in {args.file}")

    prefix = args.prefix.rstrip("/")
    for key in sorted(parameters):
        value = parameters[key]
        if value == "":
            if args.skip_empty:
                print(f"skip {prefix}/{key} (empty)")
                continue
            value = args.empty_placeholder
            print(f"note {prefix}/{key} was empty — storing placeholder {value!r}")
        param_type = "SecureString" if is_secure(key) else "String"
        put_parameter(
            region=args.region,
            name=f"{prefix}/{key}",
            value=value,
            param_type=param_type,
            dry_run=args.dry_run,
        )

    print(f"Done: {len(parameters)} key(s) processed from {args.file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
