from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from sqlalchemy import select

from backend.app.infrastructure.announcements.publication_audit_repository import (
    PublicationAuditEventModel,
    SqlAlchemyPublicationAuditRepository,
)
from backend.app.infrastructure.announcements.sqlalchemy_publication_execution_repository import (
    PublicationExecutionRecordModel,
    SqlAlchemyPublicationExecutionRepository,
)
from backend.app.infrastructure.persistence.database import (
    Base,
    create_async_database_engine,
    create_async_session_factory,
)


def _require_database_url() -> None:
    from dotenv import load_dotenv

    load_dotenv()

    import os

    if not os.getenv("DATABASE_URL"):
        pytest.skip(
            "DATABASE_URL is not configured for PostgreSQL integration tests."
        )


@pytest.mark.asyncio
async def test_shared_async_persistence_factory_uses_canonical_base() -> None:
    """Verify WS-22 repositories use the canonical persistence boundary."""

    _require_database_url()

    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)

    try:
        assert engine is not None
        assert session_factory is not None

        # Both WS-22 models must belong to the canonical platform metadata.
        assert (
            PublicationExecutionRecordModel.metadata
            is Base.metadata
        )
        assert (
            PublicationAuditEventModel.metadata
            is Base.metadata
        )

        # The repositories must accept the canonical async factory.
        execution_repository = SqlAlchemyPublicationExecutionRepository(
            session_factory
        )
        audit_repository = SqlAlchemyPublicationAuditRepository(
            session_factory
        )

        assert execution_repository is not None
        assert audit_repository is not None

    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_shared_async_session_reaches_same_postgresql_database() -> None:
    """Verify the canonical async factory can execute against PostgreSQL."""

    _require_database_url()

    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)

    try:
        async with session_factory() as session:
            result = await session.execute(select(1))
            assert result.scalar_one() == 1

    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_execution_and_audit_repositories_share_same_session_boundary() -> None:
    """Verify execution and audit repositories use the same injected factory."""

    _require_database_url()

    engine = create_async_database_engine()
    session_factory = create_async_session_factory(engine)

    try:
        execution_repository = SqlAlchemyPublicationExecutionRepository(
            session_factory
        )
        audit_repository = SqlAlchemyPublicationAuditRepository(
            session_factory
        )

        # The important architectural assertion is that both adapters receive
        # the same canonical session factory rather than creating their own.
        assert execution_repository._session_factory is session_factory
        assert audit_repository._session_factory is session_factory

    finally:
        await engine.dispose()