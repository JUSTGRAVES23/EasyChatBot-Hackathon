from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.announcements.execution.approved_publication_execution import (
    ApprovedPublicationExecutionService,
)
from app.application.announcements.execution.contracts import (
    PublicationExecutionStatus,
)
from app.domain.announcements.publication import Publication
from app.domain.announcements.template_models import (
    PublicationStatus,
    PublicationType,
)


class FakeDurableExecution:
    def __init__(self) -> None:
        self.calls = []

    async def execute(self, *, publication, request):
        self.calls.append((publication, request))
        return type(
            "Result",
            (),
            {
                "status": PublicationExecutionStatus.SUCCEEDED,
            },
        )()


def make_publication(
    *,
    status: PublicationStatus = PublicationStatus.APPROVED,
) -> Publication:
    return Publication(
        publication_id=str(uuid4()),
        template_id="beta-update",
        template_version=1,
        publication_type=PublicationType.BETA_UPDATE,
        title="Beta update",
        content="Test announcement",
        status=status,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_approved_publication_delegates_to_existing_ws22_service() -> None:
    durable = FakeDurableExecution()
    service = ApprovedPublicationExecutionService(
        durable_execution=durable,
    )

    publication = make_publication()

    result = await service.execute(
        publication=publication,
        actor="admin-test",
        idempotency_key="ws23-1-4-test-key",
        correlation_id="ws23-1-4-correlation",
    )

    assert result.status is PublicationExecutionStatus.SUCCEEDED
    assert len(durable.calls) == 1
    _, request = durable.calls[0]
    assert request.actor == "admin-test"
    assert request.idempotency_key == "ws23-1-4-test-key"
    assert request.correlation_id == "ws23-1-4-correlation"


@pytest.mark.asyncio
async def test_non_uuid_publication_id_is_rejected_at_ws22_boundary() -> None:
    durable = FakeDurableExecution()
    service = ApprovedPublicationExecutionService(
        durable_execution=durable,
    )

    publication = Publication(
        publication_id="ws23-publication-001",
        template_id="beta-update",
        template_version=1,
        publication_type=PublicationType.BETA_UPDATE,
        title="Beta update",
        content="Test announcement",
        status=PublicationStatus.APPROVED,
    )

    with pytest.raises(
        ValueError,
        match="Approved publication ID must be a UUID",
    ):
        await service.execute(
            publication=publication,
            actor="admin-test",
            idempotency_key="ws23-1-4-test-key",
            correlation_id="ws23-1-4-correlation",
        )

    assert durable.calls == []


@pytest.mark.asyncio
async def test_non_approved_publication_is_not_sent_directly() -> None:
    durable = FakeDurableExecution()
    service = ApprovedPublicationExecutionService(
        durable_execution=durable,
    )

    publication = make_publication(
        status=PublicationStatus.PENDING_APPROVAL,
    )

    # The integration boundary itself does not bypass WS-22. The canonical
    # durable service remains responsible for enforcing approved-only execution.
    class RejectingDurableExecution:
        async def execute(self, *, publication, request):
            raise ValueError("Only approved publications may be executed.")

    service = ApprovedPublicationExecutionService(
        durable_execution=RejectingDurableExecution(),
    )

    with pytest.raises(
        ValueError,
        match="Only approved publications may be executed",
    ):
        await service.execute(
            publication=publication,
            actor="admin-test",
            idempotency_key="ws23-1-4-test-key",
            correlation_id="ws23-1-4-correlation",
        )

