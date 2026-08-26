from datetime import datetime, timezone

import pytest

from backend.app.application.announcements.approval.approval_service import (
    AnnouncementPublicationApprovalService,
)
from backend.app.application.announcements.publication_service import (
    AnnouncementPublicationService,
)
from backend.app.application.announcements.template_registry import (
    AnnouncementTemplateRegistry,
)
from backend.app.domain.announcements.publication import Publication
from backend.app.domain.announcements.template_models import (
    PublicationStatus,
    PublicationType,
)
from backend.app.infrastructure.announcements.in_memory_repositories import (
    InMemoryAnnouncementTemplateRepository,
    InMemoryPublicationRepository,
)


class AuditRecorder:
    def __init__(self) -> None:
        self.events = []

    async def record_approval(self, **kwargs) -> None:
        self.events.append(kwargs)


def make_publication(status: PublicationStatus) -> Publication:
    return Publication(
        publication_id="ws23-1-3-test",
        template_id="beta-update",
        template_version=1,
        publication_type=PublicationType.BETA_UPDATE,
        title="Beta update",
        content="Test announcement",
        status=status,
        created_at=datetime.now(timezone.utc),
    )


def make_publication_service(
    repository: InMemoryPublicationRepository,
) -> AnnouncementPublicationService:
    template_repository = InMemoryAnnouncementTemplateRepository()
    templates = AnnouncementTemplateRegistry(
        repository=template_repository,
    )

    return AnnouncementPublicationService(
        templates=templates,
        publications=repository,
    )


@pytest.mark.asyncio
async def test_approval_moves_pending_publication_to_approved() -> None:
    repo = InMemoryPublicationRepository()
    publication = make_publication(PublicationStatus.PENDING_APPROVAL)
    repo.save(publication)

    service = make_publication_service(repo)

    audit = AuditRecorder()
    approval = AnnouncementPublicationApprovalService(
        publications=service,
        audit=audit,
    )

    result = await approval.approve(
        publication_id=publication.publication_id,
        actor="admin-test",
    )

    assert result.publication.status is PublicationStatus.APPROVED
    assert result.publication.approved_at is not None
    assert len(audit.events) == 1
    assert audit.events[0]["actor"] == "admin-test"


@pytest.mark.asyncio
async def test_approval_rejects_invalid_lifecycle_transition() -> None:
    repo = InMemoryPublicationRepository()
    publication = make_publication(PublicationStatus.DRAFT)
    repo.save(publication)

    service = make_publication_service(repo)

    audit = AuditRecorder()
    approval = AnnouncementPublicationApprovalService(
        publications=service,
        audit=audit,
    )

    with pytest.raises(ValueError, match="Invalid publication transition"):
        await approval.approve(
            publication_id=publication.publication_id,
            actor="admin-test",
        )

    assert audit.events == []