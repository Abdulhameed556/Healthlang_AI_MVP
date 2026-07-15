"""SQLAlchemy unit-of-work (commit shared session)."""
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.users.ports.unit_of_work import IUnitOfWork


class SqlAlchemyUnitOfWork(IUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def __aenter__(self) -> "SqlAlchemyUnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            await self._session.commit()
        else:
            await self._session.rollback()
