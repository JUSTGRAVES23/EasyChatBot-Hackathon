from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

import pytest

from backend.app.application.announcements.execution.contracts import (
    PublicationExecutionRequest,
    PublicationExecutionStatus,
)
from backend.app.application.announcements.execution.durable_contracts import (
    DurableExecutionStatus,
)
from backend.app.application.announcements.execution.durable_execution_service import (
    DurablePublicationExecutionService,
)
from backend.app.domain.announcements.publication_status import PublicationStatus


@dataclass
class Publication:
    id: object
    status: PublicationStatus = PublicationStatus.APPROVED
    title: str = "Beta 2"
    content: str = "Release"

    def begin_publish(self):
        self.status = PublicationStatus.PUBLISHING

    def publish_success(self, provider_message_id=None):
        self.status = PublicationStatus.PUBLISHED

    def mark_failure(self, reason):
        self.status = PublicationStatus.FAILED


@dataclass
class Record:
    publication_id: object
    idempotency_key: str
    correlation_id: str
    attempt: int
    status: DurableExecutionStatus
    provider_message_id: str | None = None
    error_code: str | None = None


class DurableFakeRepository:
    """Persists state in a shared object, simulating a restart."""

    def __init__(self, store=None):
        self.store = store if store is not None else {}

    async def get_by_idempotency_key(self, key):
        return self.store.get(key)

    async def create_started(self, *, publication_id, idempotency_key, correlation_id):
        if idempotency_key in self.store:
            raise RuntimeError("duplicate idempotency key")
        record = Record(
            publication_id=publication_id,
            idempotency_key=idempotency_key,
            correlation_id=correlation_id,
            attempt=1,
            status=DurableExecutionStatus.STARTED,
        )
        self.store[idempotency_key] = record
        return record

    async def mark_succeeded(self, *, idempotency_key, provider_message_id):
        record = self.store[idempotency_key]
        record.status = DurableExecutionStatus.SUCCEEDED
        record.provider_message_id = provider_message_id
        return record

    async def mark_failed(self, *, idempotency_key, error_code):
        record = self.store[idempotency_key]
        record.status = DurableExecutionStatus.FAILED
        record.error_code = error_code
        return record


class Publisher:
    def __init__(self):
        self.calls = 0

    async def publish(self, **kwargs):
        self.calls += 1
        return "telegram-independent-provider-id"


class Audit:
    def __init__(self):
        self.success = []
        self.failure = []

    async def record_success(self, **kwargs):
        self.success.append(kwargs)

    async def record_failure(self, **kwargs):
        self.failure.append(kwargs)


def req(pid):
    return PublicationExecutionRequest(
        publication_id=pid,
        idempotency_key="durable-001",
        actor="admin",
        correlation_id="corr-001",
    )


@pytest.mark.asyncio
async def test_duplicate_is_detected_after_service_restart():
    store = {}
    publisher = Publisher()
    audit = Audit()
    publication = Publication(uuid4())

    service_one = DurablePublicationExecutionService(
        publisher=publisher,
        execution_repository=DurableFakeRepository(store),
        audit=audit,
    )
    first = await service_one.execute(
        publication=publication,
        request=req(publication.id),
    )

    # New service instance: no in-memory idempotency state survives here.
    service_two = DurablePublicationExecutionService(
        publisher=publisher,
        execution_repository=DurableFakeRepository(store),
        audit=audit,
    )
    second = await service_two.execute(
        publication=publication,
        request=req(publication.id),
    )

    assert first.status is PublicationExecutionStatus.SUCCEEDED
    assert second.status is PublicationExecutionStatus.IDEMPOTENT_REPLAY
    assert publisher.calls == 1


@pytest.mark.asyncio
async def test_success_is_durably_recorded():
    store = {}
    publisher = Publisher()
    audit = Audit()
    publication = Publication(uuid4())

    service = DurablePublicationExecutionService(
        publisher=publisher,
        execution_repository=DurableFakeRepository(store),
        audit=audit,
    )

    await service.execute(publication=publication, request=req(publication.id))

    record = store["durable-001"]
    assert record.status is DurableExecutionStatus.SUCCEEDED
    assert record.provider_message_id == "telegram-independent-provider-id"
    assert record.correlation_id == "corr-001"


@pytest.mark.asyncio
async def test_failed_attempt_is_durably_recorded_without_sensitive_error_text():
    class FailingPublisher:
        async def publish(self, **kwargs):
            raise RuntimeError("secret provider response: APIKEY=DO_NOT_STORE")

    store = {}
    audit = Audit()
    publication = Publication(uuid4())

    service = DurablePublicationExecutionService(
        publisher=FailingPublisher(),
        execution_repository=DurableFakeRepository(store),
        audit=audit,
    )

    result = await service.execute(
        publication=publication,
        request=req(publication.id),
    )

    assert result.status is PublicationExecutionStatus.FAILED
    record = store["durable-001"]
    assert record.status is DurableExecutionStatus.FAILED
    assert record.error_code == "RUNTIMEERROR"
    assert "APIKEY" not in str(record)
