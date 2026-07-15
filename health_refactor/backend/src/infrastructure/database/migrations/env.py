"""Alembic migration environment (async SQLAlchemy + asyncpg)."""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from backend.src.core.config import settings
from backend.src.infrastructure.database.base import Base

# Import models package so all tables register on Base.metadata before autogenerate.
import backend.src.infrastructure.database.models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Separate version table when multiple apps share one Postgres DB.
VERSION_TABLE = "alembic_version_backend"

# Admin ORM models use a separate SQLAlchemy Base; keep their tables out of
# backend autogenerate. Add admin schema changes as hand-written revisions here.
IGNORED_TABLES = frozenset(
    {
        "alembic_version",
        "admin_users",
        "admin_sessions",
        "admin_invitations",
        "admin_otps",
    }
)


def include_object(object, name, type_, reflected, compare_to):
    """Exclude admin-owned tables from autogenerate when DB is shared with admin."""
    if type_ == "table" and name in IGNORED_TABLES:
        return False
    return True


def _configure_context(**kwargs):
    return dict(
        target_metadata=target_metadata,
        version_table=VERSION_TABLE,
        include_object=include_object,
        **kwargs,
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        **_configure_context(
            url=settings.database_url,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, **_configure_context())

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
