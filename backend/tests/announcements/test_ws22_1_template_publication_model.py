from __future__ import annotations

import pytest

from backend.app.application.announcements.audit import (
    AnnouncementAuditEventType,
    InMemoryAnnouncementAuditSink,
)
from backend.app.application.announcements.publication_service import AnnouncementPublicationService
from backend.app.application.announcements.template_registry import AnnouncementTemplateRegistry
from backend.app.domain.announcements.publication import Publication
from backend.app.domain.announcements.template_models import (
    AnnouncementTemplate,
    AnnouncementTemplateVersion,
    PublicationStatus,
    PublicationType,
)
from backend.app.infrastructure.announcements.in_memory_repositories import (
    InMemoryAnnouncementTemplateRepository,
    InMemoryPublicationRepository,
)


def make_template(version: int = 1) -> AnnouncementTemplate:
    tv = AnnouncementTemplateVersion(
        template_id="beta-update",
        version=version,
        publication_type=PublicationType.BETA_UPDATE,
        structure=(
            "🌱 EasyWorld — Growing with You",
            "",
            "BETA UPDATE",
            "",
            "{{title}}",
            "",
            "{{body}}",
            "",
            "{{timing}}",
        ),
        required_fields=frozenset({"title", "body"}),
        optional_fields=frozenset({"timing"}),
    )
    return AnnouncementTemplate(
        template_id="beta-update",
        name="Beta Update",
        publication_type=PublicationType.BETA_UPDATE,
        active_version=version,
        versions=(tv,),
    )


def make_service():
    template_repo = InMemoryAnnouncementTemplateRepository()
    registry = AnnouncementTemplateRegistry(template_repo)
    registry.register(make_template())
    publication_repo = InMemoryPublicationRepository()
    service = AnnouncementPublicationService(
        templates=registry,
        publications=publication_repo,
    )
    return service, registry, publication_repo


def test_required_template_fields_are_enforced():
    _, registry, _ = make_service()
    with pytest.raises(ValueError, match="Missing required"):
        registry.preview(template_id="beta-update", values={"title": "X"})


def test_publication_captures_version_and_content_snapshot():
    service, _, repo = make_service()
    publication = service.create(
        publication_id="pub-001",
        template_id="beta-update",
        title="Beta 2",
        values={"title": "Beta 2", "body": "A new beta is available.", "timing": "Today"},
    )
    assert publication.template_id == "beta-update"
    assert publication.template_version == 1
    assert "A new beta is available." in publication.content
    assert repo.get("pub-001").content == publication.content


def test_publication_lifecycle_is_controlled():
    service, _, repo = make_service()
    service.create(
        publication_id="pub-002",
        template_id="beta-update",
        title="Maintenance",
        values={"title": "Maintenance", "body": "Scheduled maintenance."},
    )
    service.request_approval("pub-002")
    service.approve("pub-002")
    service.begin_publish("pub-002")
    service.mark_publish_success("pub-002")
    stored = repo.get("pub-002")
    assert stored.status is PublicationStatus.PUBLISHED
    assert stored.published_at is not None


def test_failed_publication_records_reason():
    service, _, repo = make_service()
    service.create(
        publication_id="pub-003",
        template_id="beta-update",
        title="Announcement",
        values={"title": "Announcement", "body": "Content"},
    )
    service.request_approval("pub-003")
    service.approve("pub-003")
    service.begin_publish("pub-003")
    service.mark_publish_failure("pub-003", "Telegram timeout")
    stored = repo.get("pub-003")
    assert stored.status is PublicationStatus.FAILED
    assert stored.failure_reason == "Telegram timeout"


def test_invalid_transition_is_rejected():
    publication = Publication(
        publication_id="pub-004",
        template_id="beta-update",
        template_version=1,
        publication_type=PublicationType.BETA_UPDATE,
        title="Test",
        content="Content",
    )
    with pytest.raises(ValueError, match="Invalid publication transition"):
        publication.publish_success()


def test_audit_sink_records_events():
    sink = InMemoryAnnouncementAuditSink()
    sink.record("pub-005", AnnouncementAuditEventType.CREATED)
    sink.record("pub-005", AnnouncementAuditEventType.APPROVED)
    sink.record("pub-005", AnnouncementAuditEventType.PUBLISH_FAILED, "Telegram timeout")
    events = sink.list_for("pub-005")
    assert [e.event_type for e in events] == [
        AnnouncementAuditEventType.CREATED,
        AnnouncementAuditEventType.APPROVED,
        AnnouncementAuditEventType.PUBLISH_FAILED,
    ]
    assert events[-1].details == "Telegram timeout"
