"""Unit tests: core/pagination.py"""
from backend.src.core.pagination import PaginatedResponse, PaginationParams, total_pages


def test_pagination_params_defaults() -> None:
    params = PaginationParams()
    assert params.page == 1
    assert params.page_size == 20


def test_paginated_response_holds_items_and_totals() -> None:
    page = PaginatedResponse[str](
        items=["a", "b"],
        total=10,
        page=1,
        page_size=2,
        total_pages=5,
    )
    assert page.items == ["a", "b"]
    assert page.total == 10
    assert page.total_pages == 5


def test_total_pages_returns_zero_when_empty() -> None:
    assert total_pages(0, 20) == 0


def test_total_pages_rounds_up() -> None:
    assert total_pages(21, 20) == 2
