from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.app.infrastructure.announcements.publication_audit_repository import (
    PublicationAuditEventModel,
    SqlAlchemyPublicationAuditRepository,
)


def _load_repository_environment() -> None:
    """Load the repository root .env for integration tests."""

    repository_root = Path(__file__).resolve().parents[3]
    env_file = repository_root / ".env"

    load_dotenv(env_file, override=False)


def _database_url() -> str:
    _load_repository_environment()

    value = os.getenv("DATABASE_URL")

    if not value:
        pytest.fail(
            "DATABASE_URL is not available after loading the repository .env."
        )

    if value.startswith("postgresql+asyncpg://"):
        return value

    if value.startswith("postgresql://"):
        return value.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

    pytest.fail("DATABASE_URL is not a PostgreSQL URL.")


@pytest.mark.asyncio
async def test_success_audit_survives_new_repository_instance() -> None:
    engine = create_async_engine(
        _database_url(),
        pool_pre_ping=True,
    )

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    publication_id = uuid4()

    try:
        repository_1 = SqlAlchemyPublicationAuditRepository(
            session_factory
        )

        await repository_1.record_success(
            publication_id=publication_id,
            actor="integration-test",
            correlation_id="corr-success",
            provider_message_id="provider-123",
        )

        # Simulated application restart:
        # create a completely new repository instance.
        repository_2 = SqlAlchemyPublicationAuditRepository(
            session_factory
        )

        events = await repository_2.list_for(publication_id)

        assert len(events) == 1

        event = events[0]

        assert event.publication_id == str(publication_id)
        assert event.event_type == "published"
        assert event.actor == "integration-test"
        assert event.correlation_id == "corr-success"
        assert event.provider_message_id == "provider-123"
        assert event.error_code is None
        assert event.occurred_at is not None

    finally:
        async with session_factory() as session:
            await session.execute(
                delete(PublicationAuditEventModel).where(
                    PublicationAuditEventModel.publication_id
                    == str(publication_id)
                )
            )
            await session.commit()

        await engine.dispose()


@pytest.mark.asyncio
async def test_failure_audit_persists_error_code() -> None:
    engine = create_async_engine(
        _database_url(),
        pool_pre_ping=True,
    )

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    publication_id = uuid4()

    try:
        repository = SqlAlchemyPublicationAuditRepository(
            session_factory
        )

        await repository.record_failure(
            publication_id=publication_id,
            actor="integration-test",
            correlation_id="corr-failure",
            error_code="PROVIDER_TIMEOUT",
        )

        # New repository instance verifies persistence is not held
        # only in the original repository object.
        repository_2 = SqlAlchemyPublicationAuditRepository(
            session_factory
        )

        events = await repository_2.list_for(publication_id)

        assert len(events) == 1

        event = events[0]

        assert event.publication_id == str(publication_id)
        assert event.event_type == "publish_failed"
        assert event.actor == "integration-test"
        assert event.correlation_id == "corr-failure"
        assert event.error_code == "PROVIDER_TIMEOUT"
        assert event.provider_message_id is None
        assert event.occurred_at is not None

    finally:
        async with session_factory() as session:
            await session.execute(
                delete(PublicationAuditEventModel).where(
                    PublicationAuditEventModel.publication_id
                    == str(publication_id)
                )
            )
            await session.commit()

        await engine.dispose()