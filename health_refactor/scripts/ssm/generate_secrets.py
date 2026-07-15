#!/usr/bin/env python3
"""Generate secret values for SupportOS prod SSM / .env.

Outputs JWT keys, Fernet encryption key, and optional shared internal API keys.
"""
from __future__ import annotations

import argparse
import json
import secrets
import sys

from cryptography.fernet import Fernet


def generate_secrets(*, include_internal_keys: bool) -> dict[str, str]:
    internal = secrets.token_hex(32)
    out: dict[str, str] = {
        "JWT_SECRET_KEY": secrets.token_hex(32),
        "ADMIN_JWT_SECRET_KEY": secrets.token_hex(32),
        "API_TOOL_SECRETS_ENCRYPTION_KEY": Fernet.generate_key().decode(),
    }
    if include_internal_keys:
        out.update(
            {
                "INTERNAL_API_KEY": internal,
                "BACKEND_INTERNAL_API_KEY": internal,
                "AI_SERVICE_INTERNAL_API_KEY": internal,
                "ADMIN_INTERNAL_API_KEY": internal,
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("json", "env"),
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--include-internal-keys",
        action="store_true",
        help="Also generate INTERNAL_API_KEY and related shared internal keys",
    )
    args = parser.parse_args()

    values = generate_secrets(include_internal_keys=args.include_internal_keys)

    if args.format == "json":
        print(json.dumps(values, indent=2))
    else:
        for key, value in values.items():
            print(f"{key}={value}")

    print(
        "\n# Paste into scripts/ssm/supportos-prod.parameters.json, then upload.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
