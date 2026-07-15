"""Dramatiq worker entrypoint.

Run the background worker by pointing Dramatiq at THIS module::

    dramatiq ai.src.infrastructure.workers.worker --processes 1 --threads 8

Why a dedicated entrypoint (and not ``broker`` directly)?

Each Dramatiq task runs in its own short-lived asyncio event loop. A pooled
database connection is pinned to the loop that opened it, so reusing it from a
later task's loop raises "Event loop is closed" / "attached to a different loop".
We avoid that by running the worker's engine with ``NullPool`` (a fresh
connection per checkout). The flag must be set BEFORE any module imports the
database engine, which is created at import time.

The API server imports ``broker`` (via ``enqueue``) only to publish jobs, and it
runs on a single long-lived loop where pooling is correct — so it must keep its
normal pool. Setting the flag here, in a module only the worker process loads,
keeps the change scoped to the worker.
"""
import os

# Must run before any backend module imports the SQLAlchemy engine.
os.environ.setdefault("DATABASE_USE_NULL_POOL", "true")

import ai.src.infrastructure.workers.broker  # noqa: E402,F401  (configures broker + registers actors)
