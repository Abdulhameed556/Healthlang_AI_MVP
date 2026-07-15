"""Unit tests: infrastructure/database/dependencies.py"""
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.src.infrastructure.database import dependencies as db_dependencies


@pytest.mark.asyncio
async def test_get_db_yields_session_and_commits_on_close(monkeypatch) -> None:
    fake_session = AsyncMock()
    fake_session.commit = AsyncMock()
    fake_session.rollback = AsyncMock()

    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=fake_session)
    context.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr(
        db_dependencies,
        "async_session_factory",
        MagicMock(return_value=context),
    )

    generator = db_dependencies.get_db()
    session = await generator.__anext__()
    assert session is fake_session

    with pytest.raises(StopAsyncIteration):
        await generator.__anext__()

    fake_session.commit.assert_awaited_once()
    fake_session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_db_rolls_back_on_exception(monkeypatch) -> None:
    fake_session = AsyncMock()
    fake_session.commit = AsyncMock()
    fake_session.rollback = AsyncMock()

    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=fake_session)
    context.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr(
        db_dependencies,
        "async_session_factory",
        MagicMock(return_value=context),
    )

    generator = db_dependencies.get_db()
    await generator.__anext__()

    with pytest.raises(RuntimeError, match="boom"):
        await generator.athrow(RuntimeError("boom"))

    fake_session.rollback.assert_awaited_once()
    fake_session.commit.assert_not_awaited()


def test_repository_dependency_factories_return_sqlalchemy_impls() -> None:
    session = MagicMock()
    from backend.src.infrastructure.repositories.invitations import SqlAlchemyInvitationRepository
    from backend.src.infrastructure.repositories.departments import SqlAlchemyDepartmentRepository
    from backend.src.infrastructure.repositories.password_resets import (
        SqlAlchemyPasswordResetRepository,
    )
    from backend.src.infrastructure.repositories.users import SqlAlchemyUserRepository

    assert isinstance(db_dependencies.get_department_repository(session), SqlAlchemyDepartmentRepository)
    assert isinstance(db_dependencies.get_user_repository(session), SqlAlchemyUserRepository)
    assert isinstance(db_dependencies.get_invitation_repository(session), SqlAlchemyInvitationRepository)
    assert isinstance(
        db_dependencies.get_password_reset_repository(session),
        SqlAlchemyPasswordResetRepository,
    )
