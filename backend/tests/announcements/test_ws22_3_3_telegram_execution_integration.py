from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from backend.app.application.announcements.execution.contracts import (
    PublicationExecutionRequest,
    PublicationExecutionStatus,
)
from backend.app.application.announcements.execution.durable_execution_service import (
    DurablePublicationExecutionService,
)
from backend.app.application.announcements.execution.legacy_publisher_bridge import (
    LegacyAnnouncementPublisherBridge,
)
from backend.app.infrastructure.telegram.telegram_announcement_publisher import (
    TelegramAnnouncementPublisher,
)


@dataclass
class FakeTelegramMessage:
    message_id: int


class FakeTelegramClient:
    """Deterministic Telegram transport test double."""

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    async def send_message(
        self,
        *,
        chat_id: str,
        text: str,
        parse_mode: str,
    ) -> FakeTelegramMessage:
        self.calls.append(
            {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
            }
        )

        return FakeTelegramMessage(message_id=9001)


class InMemoryExecutionRepository:
    """Minimal durable repository double for the integration test."""

    def __init__(self) -> None:
        self.records = {}

    async def get_by_idempotency_key(self, idempotency_key: str):
        return self.records.get(idempotency_key)

    async def create_started(
        self,
        *,
        publication_id,
        idempotency_key,
        correlation_id,
    ):
        from datetime import datetime, timezone

        from backend.app.application.announcements.execution.durable_contracts import (
            DurableExecutionStatus,
            PublicationExecutionRecord,
        )

        existing = self.records.get(idempotency_key)

        if existing is not None:
            return existing

        now = datetime.now(timezone.utc)

        record = PublicationExecutionRecord(
            publication_id=publication_id,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            attempt=1,
            status=DurableExecutionStatus.STARTED,
            provider_message_id=None,
            error_code=None,
            created_at=now,
            updated_at=now,
        )

        self.records[idempotency_key] = record
        return record

    async def mark_succeeded(
        self,
        *,
        idempotency_key,
        provider_message_id,
    ):
        from dataclasses import replace
        from datetime import datetime, timezone

        from backend.app.application.announcements.execution.durable_contracts import (
            DurableExecutionStatus,
        )

        record = self.records[idempotency_key]

        updated = replace(
            record,
            status=DurableExecutionStatus.SUCCEEDED,
            provider_message_id=provider_message_id,
            error_code=None,
            updated_at=datetime.now(timezone.utc),
        )

        self.records[idempotency_key] = updated
        return updated

    async def mark_failed(
        self,
        *,
        idempotency_key,
        error_code,
    ):
        from dataclasses import replace
        from datetime import datetime, timezone

        from backend.app.application.announcements.execution.durable_contracts import (
            DurableExecutionStatus,
        )

        record = self.records[idempotency_key]

        updated = replace(
            record,
            status=DurableExecutionStatus.FAILED,
            error_code=error_code,
            updated_at=datetime.now(timezone.utc),
        )

        self.records[idempotency_key] = updated
        return updated


class RecordingAudit:
    def __init__(self) -> None:
        self.successes: list[dict] = []
        self.failures: list[dict] = []

    async def record_success(self, **kwargs) -> None:
        self.successes.append(kwargs)

    async def record_failure(self, **kwargs) -> None:
        self.failures.append(kwargs)


@dataclass
class ApprovedPublication:
    id: object
    title: str = "Beta 2"
    content: str = "EasyChatBot Beta 2 is available."
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


@pytest.mark.asyncio
async def test_ws22_3_3_executes_through_telegram_adapter() -> None:
    telegram_client = FakeTelegramClient()

    telegram_publisher = TelegramAnnouncementPublisher(
        telegram_client=telegram_client,
    )

    bridge = LegacyAnnouncementPublisherBridge(
        publisher=telegram_publisher,
        channel_id="-100123456789",
    )

    repository = InMemoryExecutionRepository()
    audit = RecordingAudit()

    service = DurablePublicationExecutionService(
        publisher=bridge,
        execution_repository=repository,
        audit=audit,
    )

    publication_id = uuid4()

    request = PublicationExecutionRequest(
        publication_id=publication_id,
        idempotency_key=f"ws22-3-3-{uuid4()}",
        actor="integration-test",
        correlation_id=f"corr-{uuid4()}",
    )

    publication = ApprovedPublication(
        id=publication_id,
    )

    result = await service.execute(
        publication=publication,
        request=request,
    )

    assert result.status is PublicationExecutionStatus.SUCCEEDED
    assert result.provider_message_id == "9001"

    assert len(telegram_client.calls) == 1
    assert telegram_client.calls[0] == {
        "chat_id": "-100123456789",
        "text": (
            "Beta 2\n\n"
            "EasyChatBot Beta 2 is available."
        ),
        "parse_mode": "Markdown",
    }

    persisted = await repository.get_by_idempotency_key(
        request.idempotency_key
    )

    assert persisted is not None
    assert persisted.provider_message_id == "9001"
    assert persisted.correlation_id == request.correlation_id
    assert persisted.publication_id == publication_id

    assert len(audit.successes) == 1
    assert audit.successes[0]["publication_id"] == publication_id
    assert audit.successes[0]["actor"] == "integration-test"
    assert (
        audit.successes[0]["correlation_id"]
        == request.correlation_id
    )
    assert (
        audit.successes[0]["provider_message_id"]
        == "9001"
    )


@pytest.mark.asyncio
async def test_ws22_3_3_idempotency_prevents_second_telegram_send() -> None:
    telegram_client = FakeTelegramClient()

    telegram_publisher = TelegramAnnouncementPublisher(
        telegram_client=telegram_client,
    )

    bridge = LegacyAnnouncementPublisherBridge(
        publisher=telegram_publisher,
        channel_id="-100123456789",
    )

    repository = InMemoryExecutionRepository()
    audit = RecordingAudit()

    service = DurablePublicationExecutionService(
        publisher=bridge,
        execution_repository=repository,
        audit=audit,
    )

    publication_id = uuid4()

    request = PublicationExecutionRequest(
        publication_id=publication_id,
        idempotency_key=f"ws22-3-3-idempotent-{uuid4()}",
        actor="integration-test",
        correlation_id=f"corr-{uuid4()}",
    )

    first = await service.execute(
        publication=ApprovedPublication(id=publication_id),
        request=request,
    )

    second = await service.execute(
        publication=ApprovedPublication(id=publication_id),
        request=request,
    )

    assert first.status is PublicationExecutionStatus.SUCCEEDED

    assert (
        second.status
        is PublicationExecutionStatus.IDEMPOTENT_REPLAY
    )

    assert second.provider_message_id == "9001"

    # Critical WS-22 guarantee:
    # the provider receives exactly one publication.
    assert len(telegram_client.calls) == 1

    # Only the original successful execution records an audit success.
    assert len(audit.successes) == 1