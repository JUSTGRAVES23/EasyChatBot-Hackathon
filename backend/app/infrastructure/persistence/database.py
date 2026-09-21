from __future__ import annotations

import os

from sqlalchemy import Column, Table, create_engine
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Canonical SQLAlchemy metadata registry for the platform."""

    pass


# The authentication subsystem owns the physical ``users`` table and
# persists it through its raw-SQL repository.  This metadata-only table
# exists solely so SQLAlchemy can resolve foreign keys from ORM models
# that reference users.id.  It is not an ORM-mapped User entity and does
# not create or manage the physical table.
users_table = Table(
    "users",
    Base.metadata,
    Column(
        "id",
        PGUUID(as_uuid=True),
        nullable=False,
    ),
)


def database_url() -> str:
    """Return the canonical PostgreSQL connection URL."""

    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError(
            "DATABASE_URL is required for PostgreSQL persistence."
        )

    return value


def create_database_engine():
    """Create the existing synchronous PostgreSQL engine.

    This API is preserved for the existing Beta 1 persistence layer.
    """

    return create_engine(
        database_url(),
        pool_pre_ping=True,
        future=True,
    )


def create_session_factory(
    engine,
) -> sessionmaker[Session]:
    """Create the existing synchronous session factory.

    Preserved for existing Beta 1 repositories.
    """

    return sessionmaker(
        bind=engine,
        class_=Session,
        expire_on_commit=False,
    )


def async_database_url() -> str:
    """Return DATABASE_URL adapted for SQLAlchemy async PostgreSQL.

    The environment remains the single source of truth. We only adapt the
    driver at the infrastructure boundary when the configured URL uses the
    standard PostgreSQL SQLAlchemy scheme.
    """

    value = database_url()

    if value.startswith("postgresql+asyncpg://"):
        return value

    if value.startswith("postgresql://"):
        return value.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

    raise RuntimeError(
        "DATABASE_URL must use a PostgreSQL URL compatible with "
        "the synchronous or async PostgreSQL persistence boundary."
    )


def create_async_database_engine() -> AsyncEngine:
    """Create the canonical asynchronous PostgreSQL engine.

    This is used by durable WS-22 persistence while sharing the same
    DATABASE_URL and canonical Base as the existing persistence layer.
    """

    return create_async_engine(
        async_database_url(),
        pool_pre_ping=True,
    )


def create_async_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create the canonical asynchronous PostgreSQL session factory."""

    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
