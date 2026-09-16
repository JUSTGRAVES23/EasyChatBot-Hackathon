from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import delete, select

from app.application.announcements.execution.contracts import (
    PublicationExecutionRequest,
    PublicationExecutionStatus,
)
from app.application.announcements.execution.durable_execution_composition import (
    create_durable_publication_execution_composition,
)
from app.infrastructure.announcements.publication_audit_repository import (
    PublicationAuditEventModel,
)
from app.infrastructure.announcements.sqlalchemy_publication_execution_repository import (
    PublicationExecutionRecordModel,
)


def _load_repository_environment() -> None:
    load_dotenv()

    if not os.getenv("DATABASE_URL"):
        pytest.skip(
            "DATABASE_URL is not configured for PostgreSQL integration tests."
        )


class RecordingPublisher:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    async def publish(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return "provider-ws22-3-5-4-001"


@dataclass
class ApprovedPublication:
    id: UUID
    title: str = "WS-22.3.5.4 test"
    content: str = "Durable composition integration test."
    status: str = "approved"

    def begin_publish(self) -> None:
        pass

    def publish_success(
        self,
        provider_message_id: str | None = None,
    ) -> None:
        self.status = "published"

    def mark_failure(self, error_code: str) -> None:
        self.status = "failed"


async def _cleanup(
    composition,
    *,
    idempotency_key: str,
    publication_id: UUID,
) -> None:
    async with composition.session_factory() as session:
        await session.execute(
            delete(PublicationAuditEventModel).where(
                PublicationAuditEventModel.publication_id
                == str(publication_id)
            )
        )

        await session.execute(
            delete(PublicationExecutionRecordModel).where(
                PublicationExecutionRecordModel.idempotency_key
                == idempotency_key
            )
        )

        await session.commit()


@pytest.mark.asyncio
async def test_composition_executes_and_persists_execution_and_audit() -> None:
    _load_repository_environment()

    publisher = RecordingPublisher()

    composition = create_durable_publication_execution_composition(
        publisher=publisher,
    )

    publication_id = uuid4()
    idempotency_key = f"ws22-3-5-4-{uuid4()}"
    correlation_id = f"corr-{uuid4()}"

    request = PublicationExecutionRequest(
        publication_id=publication_id,
        idempotency_key=idempotency_key,
        actor="ws22-3-5-4-test",
        correlation_id=correlation_id,
    )

    publication = ApprovedPublication(id=publication_id)

    try:
        result = await composition.service.execute(
            publication=publication,
            request=request,
        )

        assert result.status is PublicationExecutionStatus.SUCCEEDED
        assert result.provider_message_id == "provider-ws22-3-5-4-001"
        assert len(publisher.calls) == 1

        async with composition.session_factory() as session:
            execution = await session.scalar(
                select(PublicationExecutionRecordModel).where(
                    PublicationExecutionRecordModel.idempotency_key
                    == idempotency_key
                )
            )

            assert execution is not None
            assert execution.idempotency_key == idempotency_key
            assert execution.correlation_id == correlation_id
            assert execution.provider_message_id == (
                "provider-ws22-3-5-4-001"
            )

            audit_events = (
                await session.scalars(
                    select(PublicationAuditEventModel)
                    .where(
                        PublicationAuditEventModel.publication_id
                        == str(publication_id)
                    )
                    .order_by(PublicationAuditEventModel.id)
                )
            ).all()

            assert len(audit_events) == 1
            assert audit_events[0].event_type == "published"
            assert audit_events[0].actor == "ws22-3-5-4-test"
            assert audit_events[0].correlation_id == correlation_id
            assert audit_events[0].provider_message_id == (
                "provider-ws22-3-5-4-001"
            )

    finally:
        await _cleanup(
            composition,
            idempotency_key=idempotency_key,
            publication_id=publication_id,
        )
        await composition.dispose()


@pytest.mark.asyncio
async def test_composition_replays_without_second_provider_call() -> None:
    _load_repository_environment()

    publisher = RecordingPublisher()

    composition = create_durable_publication_execution_composition(
        publisher=publisher,
    )

    publication_id = uuid4()
    idempotency_key = f"ws22-3-5-4-replay-{uuid4()}"
    correlation_id = f"corr-{uuid4()}"

    request = PublicationExecutionRequest(
        publication_id=publication_id,
        idempotency_key=idempotency_key,
        actor="ws22-3-5-4-test",
        correlation_id=correlation_id,
    )

    try:
        first = await composition.service.execute(
            publication=ApprovedPublication(id=publication_id),
            request=request,
        )

        second = await composition.service.execute(
            publication=ApprovedPublication(id=publication_id),
            request=request,
        )

        assert first.status is PublicationExecutionStatus.SUCCEEDED
        assert second.status is PublicationExecutionStatus.IDEMPOTENT_REPLAY

        assert second.provider_message_id == first.provider_message_id
        assert len(publisher.calls) == 1

    finally:
        await _cleanup(
            composition,
            idempotency_key=idempotency_key,
            publication_id=publication_id,
        )
        await composition.dispose()
