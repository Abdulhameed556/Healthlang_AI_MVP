"""Unit tests: presentation/bootstrap.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI

from ai.src.presentation.bootstrap import is_demo_ui_enabled, mount_demo_ui


def test_is_demo_ui_enabled_only_in_development() -> None:
    with patch("ai.src.core.config.settings.app_env", "development"):
        assert is_demo_ui_enabled() is True
    with patch("ai.src.core.config.settings.app_env", "production"):
        assert is_demo_ui_enabled() is False


def test_mount_demo_ui_skipped_in_production() -> None:
    app = FastAPI()
    with patch("ai.src.core.config.settings.app_env", "production"):
        mount_demo_ui(app)
    assert not any(getattr(route, "path", None) == "/demo" for route in app.routes)


def test_mount_demo_ui_warns_when_dir_missing_in_development() -> None:
    app = FastAPI()
    missing_dir = MagicMock()
    missing_dir.is_dir.return_value = False
    with (
        patch("ai.src.core.config.settings.app_env", "development"),
        patch("ai.src.presentation.bootstrap.DEMO_UI_DIR", missing_dir),
    ):
        mount_demo_ui(app)
    assert not any(getattr(route, "path", None) == "/demo" for route in app.routes)


@pytest.mark.asyncio
async def test_verify_ai_startup_calls_vector_store_verify() -> None:
    from ai.src.presentation.bootstrap import verify_ai_startup

    with patch(
        "ai.src.infrastructure.vector_store.session.verify_vector_store_connection",
        new_callable=AsyncMock,
    ) as mock_verify:
        await verify_ai_startup()

    mock_verify.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_ai_calls_vector_store_close() -> None:
    from ai.src.presentation.bootstrap import shutdown_ai

    with patch(
        "ai.src.infrastructure.vector_store.session.close_vector_store_connection",
        new_callable=AsyncMock,
    ) as mock_close:
        await shutdown_ai()

    mock_close.assert_called_once()
