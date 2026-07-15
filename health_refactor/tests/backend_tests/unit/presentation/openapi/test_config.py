"""Unit tests: presentation/openapi/config.py"""
from backend.src.main import app
from backend.src.presentation.openapi.config import setup_openapi


def test_backend_openapi_includes_response_envelope_description() -> None:
    app.openapi_schema = None
    setup_openapi(app)
    schema = app.openapi()

    description = schema["info"]["description"]
    assert "Response envelope" in description
    assert "`status_code`" in description


def test_backend_openapi_marks_password_reset_as_public() -> None:
    app.openapi_schema = None
    setup_openapi(app)
    schema = app.openapi()

    request_op = schema["paths"]["/api/v1/auth/password-reset/request"]["post"]
    logout_op = schema["paths"]["/api/v1/auth/logout"]["post"]

    assert request_op["security"] == []
    assert logout_op["security"] == [{"BackendAuth": []}]
