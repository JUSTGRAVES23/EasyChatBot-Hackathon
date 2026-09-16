from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import ASGITransport, AsyncClient

from app.api.announcement_operations_approval import (
    announcement_publish_permission,
    create_announcement_operations_approval_router,
)
from app.application.announcements.approval.async_approval_service import (
    AsyncAnnouncementPublicationApprovalService,
)
from app.domain.announcements.publication import Publication
from app.domain.announcements.template_models import (
    PublicationStatus,
    PublicationType,
)


class FakeAsyncRepository:
    def __init__(self, publication: Publication | None) -> None:
        self.publication = publication
        self.saved: list[Publication] = []

    async def get_async(self, publication_id: str) -> Publication | None:
        if (
            self.publication is not None
            and self.publication.publication_id == publication_id
        ):
            return self.publication
        return None

    async def save_async(self, publication: Publication) -> None:
        self.saved.append(publication)
        self.publication = publication


class AuditRecorder:
    def __init__(self) -> None:
        self.events: list[dict] = []

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


def make_principal(user_id: str = "operator-test") -> SimpleNamespace:
    return SimpleNamespace(user_id=user_id)


async def deny_announcement_publish_permission() -> None:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Permission denied.",
    )


async def allow_announcement_publish_permission() -> SimpleNamespace:
    return make_principal()


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

    app = FastAPI()

    router = create_announcement_operations_approval_router(
        approval_service=service,
    )

    app.include_router(router)

    # Override the exact authorization dependency used by the route.
    # This keeps the test isolated from the application's auth_repository
    # composition while exercising the production authorization boundary.
    app.dependency_overrides[announcement_publish_permission] = (
        deny_announcement_publish_permission
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

    assert repository.publication is not None
    assert (
        repository.publication.status
        is PublicationStatus.PENDING_APPROVAL
    )

    assert repository.saved == []
    assert audit.events == []


@pytest.mark.asyncio
async def test_api_authorized_approval_uses_authenticated_actor() -> None:
    repository = FakeAsyncRepository(make_publication())
    audit = AuditRecorder()

    service = AsyncAnnouncementPublicationApprovalService(
        publications=repository,
        audit=audit,
    )

    app = FastAPI()

    router = create_announcement_operations_approval_router(
        approval_service=service,
    )

    app.include_router(router)

    app.dependency_overrides[announcement_publish_permission] = (
        allow_announcement_publish_permission
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/announcement-operations/publications/"
            "ws23-1-3-persistence-test/approve",
            json={"actor": "attacker-controlled-actor"},
        )

    assert response.status_code == 200

    assert repository.publication is not None
    assert repository.publication.status is PublicationStatus.APPROVED

    assert len(repository.saved) == 1
    assert len(audit.events) == 1

    assert audit.events[0]["actor"] == "operator-test"
    assert audit.events[0]["actor"] != "attacker-controlled-actor"


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