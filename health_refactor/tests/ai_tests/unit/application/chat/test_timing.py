"""Unit tests: application/chat/timing.py"""
import time

from ai.src.application.chat.timing import RunTiming


def test_record_stores_elapsed_milliseconds() -> None:
    timing = RunTiming()
    started = time.perf_counter()
    time.sleep(0.01)

    timing.record("step_a", started)

    assert "step_a" in timing.steps
    assert timing.steps["step_a"] >= 5


def test_to_dict_rounds_milliseconds() -> None:
    timing = RunTiming(steps={"load": 12.3456, "total": 99.999})

    payload = timing.to_dict()

    assert payload == {"load": 12.3, "total": 100.0}
