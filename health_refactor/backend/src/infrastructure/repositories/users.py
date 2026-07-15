"""SQLAlchemy implementation of IUserRepository."""
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.domain.users.entities import User
from backend.src.domain.users.repositories import IUserRepository
from backend.src.infrastructure.database.models.user import User as UserModel
from backend.src.infrastructure.repositories._mappers import user_to_entity, user_to_model
from backend.src.infrastructure.repositories._utils import normalize_email


class SqlAlchemyUserRepository(IUserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: User) -> User:
        model = user_to_model(user)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return user_to_entity(model)

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model is not None else None

    async def get_by_email(self, email: str) -> User | None:
        users = await self.list_by_email(email)
        return users[0] if users else None

    async def list_by_email(self, email: str) -> list[User]:
        normalized = normalize_email(email)
        result = await self._session.execute(
            select(UserModel)
            .where(UserModel.email == normalized)
            .order_by(UserModel.created_at.asc())
        )
        return [user_to_entity(model) for model in result.scalars().all()]

    async def get_by_email_and_department(
        self, email: str, department_id: UUID
    ) -> User | None:
        normalized = normalize_email(email)
        result = await self._session.execute(
            select(UserModel).where(
                UserModel.email == normalized,
                UserModel.department_id == department_id,
            )
        )
        model = result.scalar_one_or_none()
        return user_to_entity(model) if model is not None else None

    async def exists_by_email(self, email: str) -> bool:
        normalized = normalize_email(email)
        result = await self._session.execute(
            select(exists().where(UserModel.email == normalized))
        )
        return bool(result.scalar())

    async def save(self, user: User) -> User:
        model = user_to_model(user)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return user_to_entity(merged)

    async def list_by_department_id(
        self,
        department_id: UUID,
        *,
        page: int,
        page_size: int,
        statuses: Sequence[str] | None = None,
    ) -> tuple[list[User], int]:
        filters = [UserModel.department_id == department_id]
        if statuses is not None:
            filters.append(UserModel.status.in_(list(statuses)))

        count_result = await self._session.execute(
            select(func.count()).select_from(UserModel).where(*filters)
        )
        total = int(count_result.scalar_one())

        offset = (page - 1) * page_size
        result = await self._session.execute(
            select(UserModel)
            .where(*filters)
            .order_by(UserModel.created_at.asc())
            .limit(page_size)
            .offset(offset)
        )
        users = [user_to_entity(model) for model in result.scalars().all()]
        return users, total
