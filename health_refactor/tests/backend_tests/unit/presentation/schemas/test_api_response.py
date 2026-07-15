"""Unit tests: presentation/schemas/api_response.py"""
from backend.src.presentation.schemas.api_response import ApiResponse, error_body, success


def test_success_builds_envelope() -> None:
    response = success({"id": "1"}, message="Created", status_code=201)

    assert response.message == "Created"
    assert response.status_code == 201
    assert response.error is False
    assert response.data == {"id": "1"}


def test_error_body_sets_error_true() -> None:
    body = error_body(message="Not found", status_code=404)

    assert body == {
        "message": "Not found",
        "status_code": 404,
        "error": True,
        "data": None,
    }


def test_api_response_accepts_typed_data() -> None:
    response = ApiResponse[str](
        message="OK",
        status_code=200,
        error=False,
        data="payload",
    )

    assert response.data == "payload"
