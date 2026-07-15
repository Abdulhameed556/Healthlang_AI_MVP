"""Dramatiq broker configuration and task registration.

Importing this module configures the global broker and registers every actor.
Both the worker process (run via
`dramatiq ai.src.infrastructure.workers.broker`) and the API process (through the
enqueue helpers in ``enqueue.py``) depend on this being imported before any task
module, because ``@dramatiq.actor`` resolves the global broker at import time.
"""
import dramatiq
from dramatiq.brokers.redis import RedisBroker

from ai.src.core.config import settings

redis_broker = RedisBroker(url=settings.dramatiq_broker_url)
dramatiq.set_broker(redis_broker)

# Import task modules so @dramatiq.actor decorators register with the broker.
from ai.src.infrastructure.workers.tasks import health_check as _health_check  # noqa: F401, E402
from ai.src.infrastructure.workers.tasks import indexing as _indexing  # noqa: F401, E402
from ai.src.infrastructure.workers.tasks import post_close as _post_close  # noqa: F401, E402
from ai.src.infrastructure.workers.tasks import (  # noqa: F401, E402
    freshchat_inbound as _freshchat_inbound,
)
from ai.src.infrastructure.workers.tasks import (  # noqa: F401, E402
    session_close_check as _session_close_check,
)

