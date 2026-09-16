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
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[dict] = []

    async def publish(self, **kwargs) -> str:
        self.calls.append(kwargs)

        if self.fail:
            error = RuntimeError("simulated provider timeout")
            error.error_code = "PROVIDER_TIMEOUT"
            raise error

        return "provider-ws22-3-5-5-retry-success"


@dataclass
class ApprovedPublication:
    id: UUID
    title: str = "WS-22.3.5.5 test"
    content: str = "Failure and retry integration test."
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
async def test_failure_is_durable_and_retry_succeeds() -> None:
    _load_repository_environment()

    publication_id = uuid4()
    idempotency_key = f"ws22-3-5-5-{uuid4()}"
    correlation_id = f"corr-{uuid4()}"

    request = PublicationExecutionRequest(
        publication_id=publication_id,
        idempotency_key=idempotency_key,
        actor="ws22-3-5-5-test",
        correlation_id=correlation_id,
    )

    composition_1 = create_durable_publication_execution_composition(
        publisher=RecordingPublisher(fail=True),
    )

    try:
        failed = await composition_1.service.execute(
            publication=ApprovedPublication(id=publication_id),
            request=request,
        )

        assert failed.status is PublicationExecutionStatus.FAILED
        assert failed.error_code == "PROVIDER_TIMEOUT"

        async with composition_1.session_factory() as session:
            execution = await session.scalar(
                select(PublicationExecutionRecordModel).where(
                    PublicationExecutionRecordModel.idempotency_key
                    == idempotency_key
                )
            )

            assert execution is not None
            assert execution.status == "failed"
            assert execution.attempt == 1
            assert execution.error_code == "PROVIDER_TIMEOUT"
            assert execution.provider_message_id is None

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
            assert audit_events[0].event_type == "publish_failed"
            assert audit_events[0].error_code == "PROVIDER_TIMEOUT"
            assert audit_events[0].correlation_id == correlation_id

    finally:
        await composition_1.dispose()

    # Simulate application restart: completely new composition.
    publisher_2 = RecordingPublisher(fail=False)

    composition_2 = create_durable_publication_execution_composition(
        publisher=publisher_2,
    )

    try:
        retry = await composition_2.service.execute(
            publication=ApprovedPublication(id=publication_id),
            request=request,
        )

        assert retry.status is PublicationExecutionStatus.SUCCEEDED
        assert retry.provider_message_id == (
            "provider-ws22-3-5-5-retry-success"
        )
        assert len(publisher_2.calls) == 1

        async with composition_2.session_factory() as session:
            execution = await session.scalar(
                select(PublicationExecutionRecordModel).where(
                    PublicationExecutionRecordModel.idempotency_key
                    == idempotency_key
                )
            )

            assert execution is not None
            assert execution.status == "succeeded"
            assert execution.attempt == 2
            assert execution.error_code is None
            assert execution.provider_message_id == (
                "provider-ws22-3-5-5-retry-success"
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

            assert len(audit_events) == 2
            assert audit_events[0].event_type == "publish_failed"
            assert audit_events[1].event_type == "published"

    finally:
        await _cleanup(
            composition_2,
            idempotency_key=idempotency_key,
            publication_id=publication_id,
        )
        await composition_2.dispose()
