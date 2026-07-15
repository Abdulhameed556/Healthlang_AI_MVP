#!/usr/bin/env python3
"""Backward-compatible wrapper — use test_single_task_agent.py structured instead."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ai.scripts.test_single_task_agent import main

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.extend(["structured", "--preset", "order"])
    elif sys.argv[1] not in ("structured", "run", "stream", "list-providers", "list-presets"):
        argv = ["structured", *sys.argv[1:]]
        if "--list-presets" in argv:
            argv = ["list-presets"]
        sys.argv = [sys.argv[0], *argv]
    main()
