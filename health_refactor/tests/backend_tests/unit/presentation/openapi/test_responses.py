"""Unit tests: presentation/openapi/responses.py"""
from fastapi import status

from backend.src.presentation.openapi.responses import ERROR_ADMIN_INTERNAL, envelope_responses
from backend.src.presentation.schemas.common import HealthData


def test_envelope_responses_includes_success_and_errors() -> None:
    documented = envelope_responses(
        HealthData,
        success_status=status.HTTP_200_OK,
        errors=ERROR_ADMIN_INTERNAL,
    )

    assert status.HTTP_200_OK in documented
    assert status.HTTP_401_UNAUTHORIZED in documented
    assert status.HTTP_409_CONFLICT in documented
    assert status.HTTP_422_UNPROCESSABLE_ENTITY in documented

    success = documented[status.HTTP_200_OK]
    assert "model" in success
    assert success["content"]["application/json"]["example"]["error"] is False

    err = documented[status.HTTP_401_UNAUTHORIZED]
    assert err["content"]["application/json"]["example"]["error"] is True
