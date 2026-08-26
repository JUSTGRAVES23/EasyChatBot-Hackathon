from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.app.api.announcement_operations_approval import (
    create_announcement_operations_approval_router,
)
from backend.app.application.announcements.approval.async_approval_service import (
    AsyncAnnouncementPublicationApprovalService,
)
from backend.app.domain.announcements.publication import Publication
from backend.app.domain.announcements.template_models import (
    PublicationStatus,
    PublicationType,
)
from backend.app.infrastructure.announcements.in_memory_repositories import (
    InMemoryPublicationRepository,
)


class FakeAsyncRepository:
    def __init__(self, publication: Publication | None) -> None:
        self.publication = publication
        self.saved = []

    async def get_async(self, publication_id: str):
        if self.publication and self.publication.publication_id == publication_id:
            return self.publication
        return None

    async def save_async(self, publication: Publication) -> None:
        self.saved.append(publication)
        self.publication = publication


class AuditRecorder:
    def __init__(self) -> None:
        self.events = []

    async def record_approval(self, **kwargs) -> None:
        self.events.append(kwargs)


def make_publication() -> Publication:
    return Publication(
        publication_id="ws23-1-3-persistence-test",
        template_id="beta-update",
        template_version=1,
        publication_type=PublicationType.BETA_UPDATE,
        title="Beta update",
        content="Test announcement",
        status=PublicationStatus.PENDING_APPROVAL,
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_async_approval_persists_state_and_audit_contract() -> None:
    repository = FakeAsyncRepository(make_publication())
    audit = AuditRecorder()
    service = AsyncAnnouncementPublicationApprovalService(
        publications=repository,
        audit=audit,
    )

    result = await service.approve(
        publication_id="ws23-1-3-persistence-test",
        actor="admin-test",
    )

    assert result.publication.status is PublicationStatus.APPROVED
    assert len(repository.saved) == 1
    assert len(audit.events) == 1
    assert audit.events[0]["actor"] == "admin-test"


@pytest.mark.asyncio
async def test_api_denies_unauthorized_approval() -> None:
    repository = FakeAsyncRepository(make_publication())
    audit = AuditRecorder()
    service = AsyncAnnouncementPublicationApprovalService(
        publications=repository,
        audit=audit,
    )

    async def deny() -> bool:
        return False

    app = FastAPI()
    app.include_router(
        create_announcement_operations_approval_router(
            approval_service=service,
            admin_authorizer=deny,
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/announcement-operations/publications/"
            "ws23-1-3-persistence-test/approve",
            json={"actor": "admin-test"},
        )

    assert response.status_code == 403
    assert repository.publication.status is PublicationStatus.PENDING_APPROVAL
    assert audit.events == []


@pytest.mark.asyncio
async def test_invalid_transition_is_rejected() -> None:
    publication = make_publication()
    publication.status = PublicationStatus.DRAFT

    repository = FakeAsyncRepository(publication)
    audit = AuditRecorder()
    service = AsyncAnnouncementPublicationApprovalService(
        publications=repository,
        audit=audit,
    )

    with pytest.raises(ValueError, match="Invalid publication transition"):
        await service.approve(
            publication_id=publication.publication_id,
            actor="admin-test",
        )

    assert repository.saved == []
    assert audit.events == []
