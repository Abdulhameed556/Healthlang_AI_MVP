"""SQLAlchemy unit-of-work (commit shared session)."""
from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession


class IUnitOfWork(Protocol):
    async def commit(self) -> None: ...


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()
