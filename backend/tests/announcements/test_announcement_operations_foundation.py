from __future__ import annotations

from uuid import UUID

import pytest

from backend.app.application.announcements.announcement_operations_service import AnnouncementOperationsService
from backend.app.application.announcements.in_memory_repositories import InMemoryAnnouncementRepository, InMemoryPublicationEventRepository
from backend.app.domain.announcements.publication_event import PublicationEventType
from backend.app.domain.announcements.publication_status import PublicationStatus


@pytest.mark.asyncio
async def test_lifecycle_and_audit_events() -> None:
    service = AnnouncementOperationsService(
        repository=InMemoryAnnouncementRepository(),
        event_repository=InMemoryPublicationEventRepository(),
    )
    item = await service.create(title="Beta 2", body="Release", actor="admin", correlation_id="ann-1")
    assert item.status is PublicationStatus.DRAFT

    await service.mark_ready_for_review(item.id, actor="admin")
    await service.approve(item.id, actor="admin")
    await service.request_publication(item.id, actor="admin")
    await service.mark_published(item.id, actor="admin", provider_message_id="tg-1")

    assert (await service.get(item.id)).status is PublicationStatus.PUBLISHED
    events = await service.audit_log(item.id)
    assert [event.event_type for event in events] == [
        PublicationEventType.CREATED,
        PublicationEventType.READY_FOR_REVIEW,
        PublicationEventType.APPROVED,
        PublicationEventType.PUBLISH_REQUESTED,
        PublicationEventType.PUBLISHED,
    ]
    assert events[-1].provider_message_id == "tg-1"


@pytest.mark.asyncio
async def test_failed_publication_is_recorded() -> None:
    service = AnnouncementOperationsService(
        repository=InMemoryAnnouncementRepository(),
        event_repository=InMemoryPublicationEventRepository(),
    )
    item = await service.create(title="Notice", body="Maintenance", actor="admin")
    await service.mark_ready_for_review(item.id, actor="admin")
    await service.approve(item.id, actor="admin")
    await service.request_publication(item.id, actor="admin")
    await service.mark_failed(item.id, actor="admin", error_code="TELEGRAM_TIMEOUT")

    assert (await service.get(item.id)).status is PublicationStatus.FAILED
    events = await service.audit_log(item.id)
    assert events[-1].event_type is PublicationEventType.FAILED
    assert events[-1].error_code == "TELEGRAM_TIMEOUT"


def test_invalid_transition_is_rejected() -> None:
    from backend.app.domain.announcements.announcement import Announcement
    item = Announcement(title="A", body="B", created_by="admin")
    with pytest.raises(ValueError):
        item.mark_published()
