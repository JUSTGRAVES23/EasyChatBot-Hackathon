from __future__ import annotations

from uuid import uuid4

import pytest

from app.application.announcements.audit import (
    AnnouncementAuditEventType,
    InMemoryAnnouncementAuditSink,
)
from app.application.announcements.execution.audit_adapter import (
    PublicationExecutionAuditAdapter,
)


@pytest.mark.asyncio
async def test_success_maps_to_published_audit_event() -> None:
    sink = InMemoryAnnouncementAuditSink()
    adapter = PublicationExecutionAuditAdapter(sink=sink)

    publication_id = uuid4()

    await adapter.record_success(
        publication_id=publication_id,
        actor="admin",
        correlation_id="corr-001",
        provider_message_id="telegram-123",
    )

    events = sink.list_for(str(publication_id))

    assert len(events) == 1

    event = events[0]

    assert event.event_type is AnnouncementAuditEventType.PUBLISHED
    assert "actor=admin" in event.details
    assert "correlation_id=corr-001" in event.details
    assert "provider_message_id=telegram-123" in event.details


@pytest.mark.asyncio
async def test_failure_maps_to_publish_failed_audit_event() -> None:
    sink = InMemoryAnnouncementAuditSink()
    adapter = PublicationExecutionAuditAdapter(sink=sink)

    publication_id = uuid4()

    await adapter.record_failure(
        publication_id=publication_id,
        actor="admin",
        correlation_id="corr-002",
        error_code="TELEGRAM_TIMEOUT",
    )

    events = sink.list_for(str(publication_id))

    assert len(events) == 1

    event = events[0]

    assert event.event_type is AnnouncementAuditEventType.PUBLISH_FAILED
    assert "actor=admin" in event.details
    assert "correlation_id=corr-002" in event.details
    assert "error_code=TELEGRAM_TIMEOUT" in event.details


def test_adapter_rejects_missing_sink() -> None:
    with pytest.raises(ValueError, match="sink cannot be None"):
        PublicationExecutionAuditAdapter(
            sink=None,  # type: ignore[arg-type]
        )
