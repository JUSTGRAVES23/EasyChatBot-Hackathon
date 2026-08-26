import pytest

from backend.app.application.announcement_operations.publication_execution_service import (
    PublicationExecutionService,
)
from app.domain.announcement_publication.execution import (
    PublishAnnouncementCommand,
    PublicationExecutionStatus,
)
from backend.app.application.announcement_operations.publication_execution_ports import (
    PublicationForExecution,
)


class FakeRepository:
    def __init__(self, publication=None):
        self.publication = publication
        self.results = []

    async def get_for_execution(self, publication_id):
        return self.publication

    async def record_execution(self, result):
        self.results.append(result)


class FakePublisher:
    def __init__(self, reference="provider-123", error=None):
        self.reference = reference
        self.error = error
        self.calls = 0

    async def publish(self, *, publication, idempotency_key):
        self.calls += 1
        if self.error:
            raise RuntimeError(self.error)
        return self.reference


class FakeIdempotencyStore:
    def __init__(self):
        self.results = {}

    async def get_result(self, idempotency_key):
        return self.results.get(idempotency_key)

    async def store_result(self, result):
        self.results[result.idempotency_key] = result


class FakeAuditSink:
    def __init__(self):
        self.events = []

    async def record(self, event):
        self.events.append(event)


def make_service(publication=None, publisher=None):
    repository = FakeRepository(publication)
    publisher = publisher or FakePublisher()
    idempotency = FakeIdempotencyStore()
    audit = FakeAuditSink()

    service = PublicationExecutionService(
        repository=repository,
        publisher=publisher,
        idempotency_store=idempotency,
        audit_sink=audit,
    )
    return service, repository, publisher, idempotency, audit


@pytest.mark.asyncio
async def test_ws22_3_1_executes_approved_publication():
    service, repository, publisher, _idempotency, audit = make_service(
        PublicationForExecution(
            publication_id="pub-001",
            status="approved",
            destination="announcement-group",
            rendered_content="Approved announcement",
        )
    )

    result = await service.execute(
        PublishAnnouncementCommand(
            publication_id="pub-001",
            idempotency_key="idem-001",
            requested_by="operator-001",
        )
    )

    assert result.status is PublicationExecutionStatus.SUCCEEDED
    assert result.provider_reference == "provider-123"
    assert publisher.calls == 1
    assert len(repository.results) == 1
    assert len(audit.events) == 1


@pytest.mark.asyncio
async def test_ws22_3_1_rejects_non_executable_publication():
    service, repository, publisher, _idempotency, audit = make_service(
        PublicationForExecution(
            publication_id="pub-002",
            status="draft",
            destination="announcement-group",
            rendered_content="Draft",
        )
    )

    result = await service.execute(
        PublishAnnouncementCommand(
            publication_id="pub-002",
            idempotency_key="idem-002",
            requested_by="operator-001",
        )
    )

    assert result.status is PublicationExecutionStatus.FAILED
    assert publisher.calls == 0
    assert len(repository.results) == 1
    assert len(audit.events) == 1


@pytest.mark.asyncio
async def test_ws22_3_1_is_idempotent():
    service, _repository, publisher, idempotency, _audit = make_service(
        PublicationForExecution(
            publication_id="pub-003",
            status="approved",
            destination="announcement-group",
            rendered_content="Approved",
        )
    )

    command = PublishAnnouncementCommand(
        publication_id="pub-003",
        idempotency_key="idem-003",
        requested_by="operator-001",
    )

    first = await service.execute(command)
    second = await service.execute(command)

    assert first.status is PublicationExecutionStatus.SUCCEEDED
    assert second.status is PublicationExecutionStatus.SUCCEEDED
    assert first.provider_reference == second.provider_reference
    assert publisher.calls == 1
    assert len(idempotency.results) == 1


@pytest.mark.asyncio
async def test_ws22_3_1_records_provider_failure():
    service, _repository, publisher, _idempotency, audit = make_service(
        PublicationForExecution(
            publication_id="pub-004",
            status="approved",
            destination="announcement-group",
            rendered_content="Approved",
        ),
        publisher=FakePublisher(error="channel unavailable"),
    )

    result = await service.execute(
        PublishAnnouncementCommand(
            publication_id="pub-004",
            idempotency_key="idem-004",
            requested_by="operator-001",
        )
    )

    assert result.status is PublicationExecutionStatus.FAILED
    assert result.error_message == "channel unavailable"
    assert len(audit.events) == 1
    assert audit.events[0].safe_metadata == {
        "execution_status": "failed"
    }


@pytest.mark.asyncio
async def test_ws22_3_1_does_not_put_content_or_secrets_in_audit_event():
    service, _repository, _publisher, _idempotency, audit = make_service(
        PublicationForExecution(
            publication_id="pub-005",
            status="approved",
            destination="announcement-group",
            rendered_content="PRIVATE CONTENT api_key=SECRET",
        )
    )

    await service.execute(
        PublishAnnouncementCommand(
            publication_id="pub-005",
            idempotency_key="idem-005",
            requested_by="operator-001",
        )
    )

    audit_payload = str(audit.events[0]).lower()

    assert "private content" not in audit_payload
    assert "secret" not in audit_payload
    assert "api_key" not in audit_payload

