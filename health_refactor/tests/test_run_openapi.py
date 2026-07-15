"""Unit tests: run.py OpenAPI security metadata."""
from backend.src.presentation.openapi.public_paths import is_public_openapi_path
from run import _custom_openapi, root_app


def test_is_public_openapi_path_recognizes_password_reset_routes() -> None:
    assert is_public_openapi_path("/api/v1/auth/password-reset/request")
    assert is_public_openapi_path("/api/v1/auth/password-reset/complete")
    assert not is_public_openapi_path("/api/v1/users/me")


def test_openapi_includes_response_envelope_description() -> None:
    root_app.openapi_schema = None
    schema = _custom_openapi()

    description = schema["info"]["description"]
    assert "Response envelope" in description
    assert "`message`" in description
    assert "`data`" in description


def test_openapi_marks_password_reset_routes_as_public() -> None:
    root_app.openapi_schema = None
    schema = _custom_openapi()

    request_op = schema["paths"]["/api/v1/auth/password-reset/request"]["post"]
    complete_op = schema["paths"]["/api/v1/auth/password-reset/complete"]["post"]
    protected_op = schema["paths"]["/api/v1/users/me"]["get"]

    assert request_op["security"] == []
    assert complete_op["security"] == []
    assert protected_op["security"] == [{"BackendAuth": []}]
