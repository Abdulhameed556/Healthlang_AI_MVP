"""Unit tests: domain/triage/esi_rules.py"""
import pytest

from backend.src.core.exceptions import ValidationError
from backend.src.domain.triage.esi_rules import (
    assert_valid_esi_level,
    assert_valid_esi_override,
    suggest_esi_level,
)

_STABLE_VITALS = dict(
    bp_systolic=120,
    bp_diastolic=80,
    pulse=75,
    respiratory_rate=16,
    temperature=37.0,
)


def test_suggest_esi_level_returns_3_for_stable_vitals() -> None:
    assert suggest_esi_level(**_STABLE_VITALS) == 3


@pytest.mark.parametrize(
    "overrides",
    [
        {"pulse": 25},
        {"pulse": 160},
        {"bp_systolic": 65},
    ],
)
def test_suggest_esi_level_returns_1_for_immediate_life_threat(overrides: dict) -> None:
    vitals = {**_STABLE_VITALS, **overrides}
    assert suggest_esi_level(**vitals) == 1


@pytest.mark.parametrize(
    "overrides",
    [
        {"pulse": 110},
        {"pulse": 45},
        {"respiratory_rate": 25},
        {"respiratory_rate": 8},
        {"bp_systolic": 85},
        {"temperature": 40.0},
        {"temperature": 34.5},
    ],
)
def test_suggest_esi_level_returns_2_for_danger_zone_vitals(overrides: dict) -> None:
    vitals = {**_STABLE_VITALS, **overrides}
    assert suggest_esi_level(**vitals) == 2


def test_immediate_threat_takes_priority_over_danger_zone() -> None:
    # pulse=160 alone is level 1; a concurrently abnormal resp rate must not
    # water it down to level 2.
    vitals = {**_STABLE_VITALS, "pulse": 160, "respiratory_rate": 25}
    assert suggest_esi_level(**vitals) == 1


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5])
def test_assert_valid_esi_level_allows_1_through_5(level: int) -> None:
    assert_valid_esi_level(level)


@pytest.mark.parametrize("level", [0, 6, -1, 100])
def test_assert_valid_esi_level_rejects_out_of_range(level: int) -> None:
    with pytest.raises(ValidationError, match="between 1 and 5"):
        assert_valid_esi_level(level)


def test_assert_valid_esi_override_allows_accepting_suggestion() -> None:
    assert_valid_esi_override(3, 3, None)


def test_assert_valid_esi_override_allows_change_with_reason() -> None:
    assert_valid_esi_override(3, 4, "Ambulatory, minor complaint, no resources needed")


def test_assert_valid_esi_override_rejects_change_without_reason() -> None:
    with pytest.raises(ValidationError, match="reason is required"):
        assert_valid_esi_override(3, 4, None)


def test_assert_valid_esi_override_rejects_change_with_empty_reason() -> None:
    with pytest.raises(ValidationError, match="reason is required"):
        assert_valid_esi_override(3, 4, "")
