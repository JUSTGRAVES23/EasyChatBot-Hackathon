from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.application.announcements.execution.contracts import (
    PublicationExecutionRequest,
    PublicationExecutionStatus,
)
from app.application.announcements.execution.durable_contracts import (
    DurableExecutionStatus,
)
from app.application.announcements.execution.durable_execution_service import (
    DurablePublicationExecutionService,
)
from app.infrastructure.announcements.sqlalchemy_publication_execution_repository import (
    PublicationExecutionRecordModel,
    SqlAlchemyPublicationExecutionRepository,
)


def _async_database_url() -> str:
    value = os.getenv("DATABASE_URL")

    if not value:
        pytest.skip(
            "DATABASE_URL is not configured for PostgreSQL integration tests."
        )

    if value.startswith("postgresql+asyncpg://"):
        return value

    if value.startswith("postgresql://"):
        return value.replace(
            "postgresql://",
            "postgresql+asyncpg://",
            1,
        )

    pytest.skip("DATABASE_URL is not a PostgreSQL URL.")


def _create_database():
    """
    Create the existing PostgreSQL connection infrastructure for this
    integration test.

    No pytest fixture is involved.
    """

    engine = create_async_engine(
        _async_database_url(),
        pool_pre_ping=True,
    )

    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return engine, session_factory


class RecordingPublisher:
    """Test-only provider boundary."""

    def __init__(
        self,
        *,
        result: str = "provider-message-1",
        fail: bool = False,
    ) -> None:
        self.result = result
        self.fail = fail
        self.calls: list[dict[str, object]] = []

    async def publish(self, **kwargs) -> str:
        self.calls.append(kwargs)

        if self.fail:
            error = RuntimeError(
                "simulated provider timeout"
            )
            error.error_code = "PROVIDER_TIMEOUT"
            raise error

        return self.result


class RecordingAudit:
    """Test-only implementation of the existing audit contract."""

    def __init__(self) -> None:
        self.successes: list[dict[str, object]] = []
        self.failures: list[dict[str, object]] = []

    async def record_success(self, **kwargs) -> None:
        self.successes.append(kwargs)

    async def record_failure(self, **kwargs) -> None:
        self.failures.append(kwargs)


@dataclass
class ApprovedPublication:
    """Minimal publication test double."""

    id: object
    title: str = "Beta release"
    content: str = "EasyChatBot Beta release."
    status: str = "approved"

    def begin_publish(self) -> None:
        self.status = "publishing"

    def publish_success(
        self,
        provider_message_id: str | None = None,
    ) -> None:
        self.status = "published"

    def mark_failure(
        self,
        error_code: str,
    ) -> None:
        self.status = "failed"


async def _delete_execution(
    session_factory: async_sessionmaker[AsyncSession],
    key: str,
) -> None:
    """Delete only the execution record created by the test."""

    async with session_factory() as session:
        await session.execute(
            delete(
                PublicationExecutionRecordModel
            ).where(
                PublicationExecutionRecordModel.idempotency_key
                == key
            )
        )

        await session.commit()


@pytest.mark.asyncio
async def test_success_survives_new_repository_and_service_instance() -> None:
    """
    Verify:

    1. Execution persists in PostgreSQL.
    2. A new repository/service instance can recover it.
    3. Duplicate execution is detected after restart.
    4. Provider message ID survives restart.
    5. Correlation ID survives restart.
    6. Provider is not called twice.
    """

    engine, session_factory = _create_database()

    key = f"ws22-3-2x1-success-{uuid4()}"
    publication_id = uuid4()
    correlation_id = f"corr-{uuid4()}"

    try:
        # ---------------------------------------------------------
        # Application instance #1
        # ---------------------------------------------------------

        publisher_1 = RecordingPublisher(
            result="provider-message-123"
        )

        audit_1 = RecordingAudit()

        repository_1 = (
            SqlAlchemyPublicationExecutionRepository(
                session_factory
            )
        )

        service_1 = DurablePublicationExecutionService(
            publisher=publisher_1,
            execution_repository=repository_1,
            audit=audit_1,
        )

        request = PublicationExecutionRequest(
            publication_id=publication_id,
            idempotency_key=key,
            correlation_id=correlation_id,
            actor="integration-test",
        )

        publication = ApprovedPublication(
            id=publication_id
        )

        result = await service_1.execute(
            publication=publication,
            request=request,
        )

        assert result.status is (
            PublicationExecutionStatus.SUCCEEDED
        )

        assert result.provider_message_id == (
            "provider-message-123"
        )

        assert len(publisher_1.calls) == 1
        assert len(audit_1.successes) == 1

        # ---------------------------------------------------------
        # Simulated application restart
        # ---------------------------------------------------------

        publisher_2 = RecordingPublisher(
            result="SHOULD-NOT-BE-SENT"
        )

        audit_2 = RecordingAudit()

        repository_2 = (
            SqlAlchemyPublicationExecutionRepository(
                session_factory
            )
        )

        service_2 = DurablePublicationExecutionService(
            publisher=publisher_2,
            execution_repository=repository_2,
            audit=audit_2,
        )

        replay = await service_2.execute(
            publication=ApprovedPublication(
                id=publication_id
            ),
            request=request,
        )

        assert replay.status is (
            PublicationExecutionStatus.IDEMPOTENT_REPLAY
        )

        assert replay.provider_message_id == (
            "provider-message-123"
        )

        # Critical guarantee.
        assert publisher_2.calls == []

        # Replay must not generate another success audit.
        assert audit_2.successes == []

        # ---------------------------------------------------------
        # Verify PostgreSQL persistence
        # ---------------------------------------------------------

        persisted = (
            await repository_2.get_by_idempotency_key(
                key
            )
        )

        assert persisted is not None

        assert persisted.status is (
            DurableExecutionStatus.SUCCEEDED
        )

        assert persisted.publication_id == (
            publication_id
        )

        assert persisted.idempotency_key == key

        assert persisted.correlation_id == (
            correlation_id
        )

        assert persisted.attempt == 1

        assert persisted.provider_message_id == (
            "provider-message-123"
        )

        assert persisted.error_code is None

    finally:
        await _delete_execution(
            session_factory,
            key,
        )

        await engine.dispose()


@pytest.mark.asyncio
async def test_failure_survives_restart_and_remains_retryable() -> None:
    """
    Verify:

    1. Failure persists in PostgreSQL.
    2. Failure survives a new repository instance.
    3. Error code persists.
    4. Correlation ID persists.
    5. Failed execution can be retried.
    6. Successful retry persists.
    """

    engine, session_factory = _create_database()

    key = f"ws22-3-2x1-failure-{uuid4()}"
    publication_id = uuid4()
    correlation_id = f"corr-{uuid4()}"

    request = PublicationExecutionRequest(
        publication_id=publication_id,
        idempotency_key=key,
        correlation_id=correlation_id,
        actor="integration-test",
    )

    try:
        # ---------------------------------------------------------
        # Initial execution â€” failure
        # ---------------------------------------------------------

        repository_1 = (
            SqlAlchemyPublicationExecutionRepository(
                session_factory
            )
        )

        publisher_1 = RecordingPublisher(
            fail=True
        )

        audit_1 = RecordingAudit()

        service_1 = DurablePublicationExecutionService(
            publisher=publisher_1,
            execution_repository=repository_1,
            audit=audit_1,
        )

        result = await service_1.execute(
            publication=ApprovedPublication(
                id=publication_id
            ),
            request=request,
        )

        assert result.status is (
            PublicationExecutionStatus.FAILED
        )

        assert result.error_code == (
            "PROVIDER_TIMEOUT"
        )

        assert len(publisher_1.calls) == 1
        assert len(audit_1.failures) == 1

        # ---------------------------------------------------------
        # Simulated restart
        # ---------------------------------------------------------

        repository_2 = (
            SqlAlchemyPublicationExecutionRepository(
                session_factory
            )
        )

        persisted = (
            await repository_2.get_by_idempotency_key(
                key
            )
        )

        assert persisted is not None

        assert persisted.status is (
            DurableExecutionStatus.FAILED
        )

        assert persisted.publication_id == (
            publication_id
        )

        assert persisted.correlation_id == (
            correlation_id
        )

        assert persisted.attempt == 1

        assert persisted.error_code == (
            "PROVIDER_TIMEOUT"
        )

        assert persisted.provider_message_id is None

        # ---------------------------------------------------------
        # Retry
        # ---------------------------------------------------------

        publisher_2 = RecordingPublisher(
            result="provider-after-retry"
        )

        audit_2 = RecordingAudit()

        service_2 = DurablePublicationExecutionService(
            publisher=publisher_2,
            execution_repository=repository_2,
            audit=audit_2,
        )

        retry = await service_2.execute(
            publication=ApprovedPublication(
                id=publication_id
            ),
            request=request,
        )

        assert retry.status is (
            PublicationExecutionStatus.SUCCEEDED
        )

        assert retry.provider_message_id == (
            "provider-after-retry"
        )

        assert len(publisher_2.calls) == 1
        assert len(audit_2.successes) == 1

        # ---------------------------------------------------------
        # Verify final PostgreSQL state
        # ---------------------------------------------------------

        persisted_after_retry = (
            await repository_2.get_by_idempotency_key(
                key
            )
        )

        assert persisted_after_retry is not None

        assert persisted_after_retry.status is (
            DurableExecutionStatus.SUCCEEDED
        )

        assert (
            persisted_after_retry.provider_message_id
            == "provider-after-retry"
        )

        assert (
            persisted_after_retry.correlation_id
            == correlation_id
        )

        assert (
            persisted_after_retry.publication_id
            == publication_id
        )

    finally:
        await _delete_execution(
            session_factory,
            key,
        )

        await engine.dispose()

