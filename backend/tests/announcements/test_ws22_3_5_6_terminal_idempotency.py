from __future__ import annotations

import os
from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest
from dotenv import load_dotenv
from sqlalchemy import delete, select

from backend.app.application.announcements.execution.contracts import (
    PublicationExecutionRequest,
    PublicationExecutionStatus,
)
from backend.app.application.announcements.execution.durable_execution_composition import (
    create_durable_publication_execution_composition,
)
from backend.app.infrastructure.announcements.publication_audit_repository import (
    PublicationAuditEventModel,
)
from backend.app.infrastructure.announcements.sqlalchemy_publication_execution_repository import (
    PublicationExecutionRecordModel,
)


def _require_database() -> None:
    load_dotenv()

    if not os.getenv("DATABASE_URL"):
        pytest.skip(
            "DATABASE_URL is not configured for PostgreSQL integration tests."
        )


class RecordingPublisher:
    def __init__(self, result: str) -> None:
        self.result = result
        self.calls: list[dict] = []

    async def publish(self, **kwargs) -> str:
        self.calls.append(kwargs)
        return self.result


@dataclass
class ApprovedPublication:
    id: UUID
    title: str = "WS-22.3.5.6 test"
    content: str = "Terminal idempotency test."
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
async def test_success_becomes_terminal_idempotent_replay() -> None:
    _require_database()

    publication_id = uuid4()
    idempotency_key = f"ws22-3-5-6-{uuid4()}"
    correlation_id = f"corr-{uuid4()}"

    request = PublicationExecutionRequest(
        publication_id=publication_id,
        idempotency_key=idempotency_key,
        actor="ws22-3-5-6-test",
        correlation_id=correlation_id,
    )

    publisher_1 = RecordingPublisher(
        result="provider-terminal-message",
    )

    composition_1 = create_durable_publication_execution_composition(
        publisher=publisher_1,
    )

    try:
        first = await composition_1.service.execute(
            publication=ApprovedPublication(id=publication_id),
            request=request,
        )

        assert first.status is PublicationExecutionStatus.SUCCEEDED
        assert first.provider_message_id == "provider-terminal-message"
        assert len(publisher_1.calls) == 1

        async with composition_1.session_factory() as session:
            execution = await session.scalar(
                select(PublicationExecutionRecordModel).where(
                    PublicationExecutionRecordModel.idempotency_key
                    == idempotency_key
                )
            )

            assert execution is not None
            assert execution.status == "succeeded"
            assert execution.attempt == 1
            assert execution.provider_message_id == (
                "provider-terminal-message"
            )
            assert execution.error_code is None

    finally:
        await composition_1.dispose()

    # Simulate a real application restart.
    publisher_2 = RecordingPublisher(
        result="MUST-NOT-BE-SENT",
    )

    composition_2 = create_durable_publication_execution_composition(
        publisher=publisher_2,
    )

    try:
        replay = await composition_2.service.execute(
            publication=ApprovedPublication(id=publication_id),
            request=request,
        )

        assert replay.status is PublicationExecutionStatus.IDEMPOTENT_REPLAY
        assert replay.provider_message_id == "provider-terminal-message"

        # Terminal success means the external provider must never be called
        # again for the same idempotency key.
        assert publisher_2.calls == []

        async with composition_2.session_factory() as session:
            execution = await session.scalar(
                select(PublicationExecutionRecordModel).where(
                    PublicationExecutionRecordModel.idempotency_key
                    == idempotency_key
                )
            )

            assert execution is not None
            assert execution.status == "succeeded"
            assert execution.attempt == 1
            assert execution.provider_message_id == (
                "provider-terminal-message"
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

            # Replay must not create another publication audit event.
            assert len(audit_events) == 1
            assert audit_events[0].event_type == "published"

    finally:
        await _cleanup(
            composition_2,
            idempotency_key=idempotency_key,
            publication_id=publication_id,
        )
        await composition_2.dispose()