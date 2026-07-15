"""Unit tests: infrastructure/repositories/users.py"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from backend.src.domain.users.entities import User
from backend.src.domain.users.value_objects import UserAuthMethod, UserRole, UserStatus
from backend.src.infrastructure.repositories._mappers import user_to_entity, user_to_model
from backend.src.infrastructure.repositories.users import SqlAlchemyUserRepository


def _scalar_result(*, one_or_none=None, scalar=None, scalar_one=None, all_models=None):
    result = MagicMock()
    result.scalar_one_or_none.return_value = one_or_none
    result.scalar.return_value = scalar
    result.scalar_one.return_value = scalar_one
    scalars = MagicMock()
    scalars.all.return_value = all_models or []
    result.scalars.return_value = scalars
    return result


@pytest.fixture()
def session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture()
def repo(session: AsyncMock) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


@pytest.mark.asyncio
async def test_add_persists_and_returns_entity(repo: SqlAlchemyUserRepository, session: AsyncMock) -> None:
    now = datetime.now(timezone.utc)
    entity = User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        role=UserRole.SUPER_ADMIN,
        status=UserStatus.INVITED,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )

    async def _refresh(model: object) -> None:
        return None

    session.refresh.side_effect = _refresh
    result = await repo.add(entity)

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    session.refresh.assert_awaited_once()
    assert result == user_to_entity(user_to_model(entity))


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_missing(
    repo: SqlAlchemyUserRepository, session: AsyncMock
) -> None:
    session.execute.return_value = _scalar_result(one_or_none=None)
    assert await repo.get_by_id(uuid4()) is None


@pytest.mark.asyncio
async def test_get_by_email_normalizes_and_maps(
    repo: SqlAlchemyUserRepository, session: AsyncMock
) -> None:
    now = datetime.now(timezone.utc)
    model = user_to_model(
        User(
            id=uuid4(),
            department_id=uuid4(),
            first_name="A",
            last_name="B",
            email="user@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            auth_method=UserAuthMethod.EMAIL_PASSWORD,
            created_at=now,
            updated_at=now,
        )
    )
    session.execute.return_value = _scalar_result(all_models=[model])

    entity = await repo.get_by_email("User@Example.com")

    assert entity is not None
    assert entity.email == "user@example.com"


@pytest.mark.asyncio
async def test_exists_by_email_returns_scalar(
    repo: SqlAlchemyUserRepository, session: AsyncMock
) -> None:
    session.execute.return_value = _scalar_result(scalar=True)
    assert await repo.exists_by_email("taken@example.com") is True


@pytest.mark.asyncio
async def test_list_by_email_returns_all_matches(
    repo: SqlAlchemyUserRepository, session: AsyncMock
) -> None:
    now = datetime.now(timezone.utc)
    models = [
        user_to_model(
            User(
                id=uuid4(),
                department_id=uuid4(),
                first_name="A",
                last_name="B",
                email="user@example.com",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                auth_method=UserAuthMethod.EMAIL_PASSWORD,
                created_at=now,
                updated_at=now,
            )
        )
    ]
    session.execute.return_value = _scalar_result(all_models=models)

    result = await repo.list_by_email("User@Example.com")

    assert len(result) == 1
    assert result[0].email == "user@example.com"


@pytest.mark.asyncio
async def test_get_by_email_and_department_returns_entity(
    repo: SqlAlchemyUserRepository, session: AsyncMock
) -> None:
    now = datetime.now(timezone.utc)
    dept_id = uuid4()
    model = user_to_model(
        User(
            id=uuid4(),
            department_id=dept_id,
            first_name="A",
            last_name="B",
            email="user@example.com",
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE,
            auth_method=UserAuthMethod.EMAIL_PASSWORD,
            created_at=now,
            updated_at=now,
        )
    )
    session.execute.return_value = _scalar_result(one_or_none=model)

    entity = await repo.get_by_email_and_department("User@Example.com", dept_id)

    assert entity is not None
    assert entity.department_id == dept_id


@pytest.mark.asyncio
async def test_save_merges_and_returns_entity(
    repo: SqlAlchemyUserRepository, session: AsyncMock
) -> None:
    now = datetime.now(timezone.utc)
    entity = User(
        id=uuid4(),
        department_id=uuid4(),
        first_name="A",
        last_name="B",
        email="user@example.com",
        role=UserRole.ADMIN,
        status=UserStatus.ACTIVE,
        auth_method=UserAuthMethod.EMAIL_PASSWORD,
        created_at=now,
        updated_at=now,
    )
    model = user_to_model(entity)
    session.merge.return_value = model

    async def _refresh(merged: object) -> None:
        return None

    session.refresh.side_effect = _refresh
    result = await repo.save(entity)

    session.merge.assert_awaited_once()
    session.flush.assert_awaited_once()
    assert result == user_to_entity(model)


@pytest.mark.asyncio
async def test_list_by_department_id_filters_by_status(
    repo: SqlAlchemyUserRepository, session: AsyncMock
) -> None:
    now = datetime.now(timezone.utc)
    model = user_to_model(
        User(
            id=uuid4(),
            department_id=uuid4(),
            first_name="A",
            last_name="B",
            email="member@example.com",
            role=UserRole.NURSE,
            status=UserStatus.ACTIVE,
            auth_method=UserAuthMethod.EMAIL_PASSWORD,
            created_at=now,
            updated_at=now,
        )
    )
    count_result = _scalar_result(scalar_one=1)
    list_result = _scalar_result(all_models=[model])
    session.execute = AsyncMock(side_effect=[count_result, list_result])

    users, total = await repo.list_by_department_id(
        model.department_id,
        page=1,
        page_size=20,
        statuses=[UserStatus.ACTIVE],
    )

    assert len(users) == 1
    assert total == 1
    assert users[0].email == "member@example.com"
