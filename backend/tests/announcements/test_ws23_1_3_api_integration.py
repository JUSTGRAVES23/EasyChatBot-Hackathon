from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.app.api.announcement_operations_approval import (
    create_announcement_operations_approval_router,
)
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
from backend.app.domain.announcements.template_models import PublicationStatus, PublicationType
from backend.app.infrastructure.announcements.in_memory_repositories import (
    InMemoryAnnouncementTemplateRepository,
    InMemoryPublicationRepository,
)


class AuditRecorder:
    def __init__(self) -> None:
        self.events: list[dict] = []

    async def record_approval(self, **kwargs) -> None:
        self.events.append(kwargs)


def make_publication(status: PublicationStatus) -> Publication:
    return Publication(
        publication_id="ws23-1-3-api-test",
        template_id="beta-update",
        template_version=1,
        publication_type=PublicationType.BETA_UPDATE,
        title="Beta update",
        content="Test announcement",
        status=status,
        created_at=datetime.now(timezone.utc),
    )


def make_service(repo: InMemoryPublicationRepository) -> AnnouncementPublicationApprovalService:
    template_repository = InMemoryAnnouncementTemplateRepository()
    templates = AnnouncementTemplateRegistry(repository=template_repository)
    publication_service = AnnouncementPublicationService(
        templates=templates,
        publications=repo,
    )
    return AnnouncementPublicationApprovalService(
        publications=publication_service,
        audit=AuditRecorder(),
    )


@pytest.mark.asyncio
async def test_approval_api_requires_administrator_authorization() -> None:
    repo = InMemoryPublicationRepository()
    publication = make_publication(PublicationStatus.PENDING_APPROVAL)
    repo.save(publication)

    service = make_service(repo)
    app = FastAPI()
    app.include_router(
        create_announcement_operations_approval_router(
            approval_service=service,
            admin_authorizer=lambda: _deny(),
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/announcement-operations/publications/{publication.publication_id}/approve",
            json={"actor": "admin-test"},
        )

    assert response.status_code == 403
    assert repo.get(publication.publication_id).status is PublicationStatus.PENDING_APPROVAL


async def _deny() -> bool:
    return False


@pytest.mark.asyncio
async def test_approval_api_approves_pending_publication() -> None:
    repo = InMemoryPublicationRepository()
    publication = make_publication(PublicationStatus.PENDING_APPROVAL)
    repo.save(publication)

    audit = AuditRecorder()
    template_repository = InMemoryAnnouncementTemplateRepository()
    templates = AnnouncementTemplateRegistry(repository=template_repository)
    publication_service = AnnouncementPublicationService(
        templates=templates,
        publications=repo,
    )
    service = AnnouncementPublicationApprovalService(
        publications=publication_service,
        audit=audit,
    )

    async def allow() -> bool:
        return True

    app = FastAPI()
    app.include_router(
        create_announcement_operations_approval_router(
            approval_service=service,
            admin_authorizer=allow,
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/announcement-operations/publications/{publication.publication_id}/approve",
            json={"actor": "admin-test"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert repo.get(publication.publication_id).status is PublicationStatus.APPROVED
    assert len(audit.events) == 1
    assert audit.events[0]["actor"] == "admin-test"


@pytest.mark.asyncio
async def test_approval_api_rejects_invalid_lifecycle_transition() -> None:
    repo = InMemoryPublicationRepository()
    publication = make_publication(PublicationStatus.DRAFT)
    repo.save(publication)

    service = make_service(repo)

    async def allow() -> bool:
        return True

    app = FastAPI()
    app.include_router(
        create_announcement_operations_approval_router(
            approval_service=service,
            admin_authorizer=allow,
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            f"/api/announcement-operations/publications/{publication.publication_id}/approve",
            json={"actor": "admin-test"},
        )

    assert response.status_code == 409
    assert repo.get(publication.publication_id).status is PublicationStatus.DRAFT
