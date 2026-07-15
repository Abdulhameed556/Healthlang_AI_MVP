"""Unit tests: infrastructure/workers/broker.py configuration.

Note: we assert broker *configuration* rather than actor membership on the
global broker. Actor registration depends on import order (Dramatiq resolves the
global broker at ``@dramatiq.actor`` decoration time), which is not deterministic
across the whole test suite. Actor existence is covered in the task tests.
"""
import dramatiq
from dramatiq.brokers.redis import RedisBroker


def test_broker_is_configured_as_global_redis_broker() -> None:
    import ai.src.infrastructure.workers.broker as broker

    assert isinstance(broker.redis_broker, RedisBroker)
    assert dramatiq.get_broker() is broker.redis_broker
