"""The Emergency Severity Index (ESI) decision tree and override rules.

This is a deliberately simplified, hand-coded stand-in for the real 5-level ESI
algorithm — not a validated clinical tool. The real algorithm splits on two
different axes: levels 1-2 are decided by acuity (how unstable is this patient
right now), while levels 3-5 are decided by anticipated resource needs (how
many tests/treatments they'll likely require) — something this system doesn't
model yet. So this suggests only levels 1, 2, or a default 3; the nurse is
expected to use clinical judgement to move a stable, low-complaint patient down
to 4 or 5 via the mandatory-reason override below.

Thresholds are the commonly cited adult "danger zone" vital signs used in ESI
training materials (tachy/bradycardia, tachypnea/bradypnea, hypotension, fever
or hypothermia) — not a substitute for one of the validated ESI v4/v5 handbooks.
"""
from backend.src.core.exceptions import ValidationError

MIN_ESI_LEVEL = 1
MAX_ESI_LEVEL = 5

_IMMEDIATE_PULSE_LOW = 30
_IMMEDIATE_PULSE_HIGH = 150
_IMMEDIATE_SYSTOLIC_LOW = 70

_DANGER_PULSE_LOW = 50
_DANGER_PULSE_HIGH = 100
_DANGER_RESP_RATE_LOW = 10
_DANGER_RESP_RATE_HIGH = 20
_DANGER_SYSTOLIC_LOW = 90
_DANGER_TEMP_LOW_C = 35.0
_DANGER_TEMP_HIGH_C = 39.5

_DEFAULT_SUGGESTED_LEVEL = 3


def suggest_esi_level(
    *,
    bp_systolic: int,
    bp_diastolic: int,
    pulse: int,
    respiratory_rate: int,
    temperature: float,
) -> int:
    """Suggest an ESI level from vitals. The nurse always confirms or overrides."""
    if pulse <= _IMMEDIATE_PULSE_LOW or pulse >= _IMMEDIATE_PULSE_HIGH:
        return 1
    if bp_systolic < _IMMEDIATE_SYSTOLIC_LOW:
        return 1

    in_danger_zone = (
        pulse > _DANGER_PULSE_HIGH
        or pulse < _DANGER_PULSE_LOW
        or respiratory_rate > _DANGER_RESP_RATE_HIGH
        or respiratory_rate < _DANGER_RESP_RATE_LOW
        or bp_systolic < _DANGER_SYSTOLIC_LOW
        or temperature >= _DANGER_TEMP_HIGH_C
        or temperature < _DANGER_TEMP_LOW_C
    )
    if in_danger_zone:
        return 2

    return _DEFAULT_SUGGESTED_LEVEL


def assert_valid_esi_level(level: int) -> None:
    """Validate a final ESI level is within the 1-5 scale."""
    if not (MIN_ESI_LEVEL <= level <= MAX_ESI_LEVEL):
        raise ValidationError(
            f"ESI level must be between {MIN_ESI_LEVEL} and {MAX_ESI_LEVEL}"
        )


def assert_valid_esi_override(
    suggested_level: int,
    final_level: int,
    override_reason: str | None,
) -> None:
    """A nurse may accept the suggested level freely, but changing it always
    requires a stated reason — full automation without override is unsafe;
    a silent override is unauditable."""
    if final_level != suggested_level and not override_reason:
        raise ValidationError(
            "An override reason is required when changing the suggested ESI level"
        )
