from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from backend.app.application.announcements.execution.contracts import (
    PublicationExecutionRequest,
    PublicationExecutionStatus,
)
from backend.app.application.announcements.execution.publication_execution_service import (
    PublicationExecutionService,
)
from backend.app.domain.announcements.publication_status import PublicationStatus


@dataclass
class FakePublication:
    id: object
    title: str = "Beta 2"
    content: str = "Release announcement"
    status: PublicationStatus = PublicationStatus.APPROVED

    def begin_publish(self) -> None:
        self.status = PublicationStatus.PUBLISHING

    def publish_success(self, provider_message_id: str | None = None) -> None:
        self.status = PublicationStatus.PUBLISHED

    def mark_failure(self, reason: str) -> None:
        self.status = PublicationStatus.FAILED


class FakePublisher:
    def __init__(self, message_id: str = "provider-1") -> None:
        self.calls = 0
        self.message_id = message_id

    async def publish(self, **kwargs) -> str:
        self.calls += 1
        return self.message_id


class FailingPublisher:
    async def publish(self, **kwargs) -> str:
        raise RuntimeError("private provider response must not be audited")


class FakeAudit:
    def __init__(self) -> None:
        self.successes = []
        self.failures = []

    async def record_success(self, **kwargs) -> None:
        self.successes.append(kwargs)

    async def record_failure(self, **kwargs) -> None:
        self.failures.append(kwargs)


def request(publication_id):
    return PublicationExecutionRequest(
        publication_id=publication_id,
        idempotency_key="exec-001",
        actor="admin",
        correlation_id="corr-001",
    )


@pytest.mark.asyncio
async def test_approved_publication_executes_and_audits_success():
    publication = FakePublication(uuid4())
    publisher = FakePublisher()
    audit = FakeAudit()
    service = PublicationExecutionService(publisher=publisher, audit=audit)

    result = await service.execute(
        publication=publication,
        request=request(publication.id),
    )

    assert result.status is PublicationExecutionStatus.SUCCEEDED
    assert result.provider_message_id == "provider-1"
    assert publication.status is PublicationStatus.PUBLISHED
    assert publisher.calls == 1
    assert len(audit.successes) == 1
    assert audit.successes[0]["provider_message_id"] == "provider-1"


@pytest.mark.asyncio
async def test_same_idempotency_key_does_not_publish_twice():
    publication = FakePublication(uuid4())
    publisher = FakePublisher()
    audit = FakeAudit()
    service = PublicationExecutionService(publisher=publisher, audit=audit)
    first = request(publication.id)

    result_one = await service.execute(publication=publication, request=first)
    result_two = await service.execute(
        publication=publication,
        request=first,
    )

    assert result_one.status is PublicationExecutionStatus.SUCCEEDED
    assert result_two.status is PublicationExecutionStatus.IDEMPOTENT_REPLAY
    assert publisher.calls == 1
    assert len(audit.successes) == 1


@pytest.mark.asyncio
async def test_non_approved_publication_is_rejected_before_publish():
    publication = FakePublication(uuid4(), status=PublicationStatus.DRAFT)
    publisher = FakePublisher()
    audit = FakeAudit()
    service = PublicationExecutionService(publisher=publisher, audit=audit)

    with pytest.raises(ValueError, match="approved"):
        await service.execute(
            publication=publication,
            request=request(publication.id),
        )

    assert publisher.calls == 0
    assert publication.status is PublicationStatus.DRAFT
    assert audit.successes == []
    assert audit.failures == []


@pytest.mark.asyncio
async def test_publisher_failure_updates_lifecycle_and_audits_stable_error_code():
    publication = FakePublication(uuid4())
    audit = FakeAudit()
    service = PublicationExecutionService(
        publisher=FailingPublisher(),
        audit=audit,
    )

    result = await service.execute(
        publication=publication,
        request=request(publication.id),
    )

    assert result.status is PublicationExecutionStatus.FAILED
    assert result.error_code == "RUNTIMEERROR"
    assert publication.status is PublicationStatus.FAILED
    assert len(audit.failures) == 1
    assert audit.failures[0]["error_code"] == "RUNTIMEERROR"
    assert "private provider response" not in str(audit.failures).lower()
