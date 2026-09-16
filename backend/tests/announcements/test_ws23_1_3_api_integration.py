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


def make_publication(status_value: PublicationStatus) -> Publication:
    return Publication(
        publication_id="ws23-1-3-api-test",
        template_id="beta-update",
        template_version=1,
        publication_type=PublicationType.BETA_UPDATE,
        title="Beta update",
        content="Test announcement",
        status=status_value,
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


def make_service(
    repository: FakeAsyncRepository,
    audit: AuditRecorder | None = None,
) -> AsyncAnnouncementPublicationApprovalService:
    return AsyncAnnouncementPublicationApprovalService(
        publications=repository,
        audit=audit or AuditRecorder(),
    )


@pytest.mark.asyncio
async def test_approval_api_requires_announcement_publish_permission() -> None:
    repository = FakeAsyncRepository(
        make_publication(PublicationStatus.PENDING_APPROVAL)
    )

    service = make_service(repository)

    app = FastAPI()
    app.include_router(
        create_announcement_operations_approval_router(
            approval_service=service,
        )
    )

    app.dependency_overrides[announcement_publish_permission] = (
        deny_announcement_publish_permission
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/announcement-operations/publications/"
            "ws23-1-3-api-test/approve",
            json={},
        )

    assert response.status_code == 403
    assert (
        repository.publication is not None
        and repository.publication.status
        is PublicationStatus.PENDING_APPROVAL
    )
    assert repository.saved == []


@pytest.mark.asyncio
async def test_approval_api_approves_pending_publication() -> None:
    repository = FakeAsyncRepository(
        make_publication(PublicationStatus.PENDING_APPROVAL)
    )
    audit = AuditRecorder()

    service = make_service(repository, audit)

    app = FastAPI()
    app.include_router(
        create_announcement_operations_approval_router(
            approval_service=service,
        )
    )

    app.dependency_overrides[announcement_publish_permission] = (
        allow_announcement_publish_permission
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/announcement-operations/publications/"
            "ws23-1-3-api-test/approve",
            json={},
        )

    assert response.status_code == 200
    assert response.json()["publication_id"] == "ws23-1-3-api-test"
    assert response.json()["status"] == "approved"

    assert repository.publication is not None
    assert repository.publication.status is PublicationStatus.APPROVED

    assert len(repository.saved) == 1
    assert len(audit.events) == 1


@pytest.mark.asyncio
async def test_approval_api_ignores_caller_supplied_actor() -> None:
    repository = FakeAsyncRepository(
        make_publication(PublicationStatus.PENDING_APPROVAL)
    )
    audit = AuditRecorder()

    service = make_service(repository, audit)

    app = FastAPI()
    app.include_router(
        create_announcement_operations_approval_router(
            approval_service=service,
        )
    )

    app.dependency_overrides[announcement_publish_permission] = (
        allow_announcement_publish_permission
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/announcement-operations/publications/"
            "ws23-1-3-api-test/approve",
            json={"actor": "attacker-controlled-actor"},
        )

    assert response.status_code == 200

    assert repository.publication is not None
    assert repository.publication.status is PublicationStatus.APPROVED

    assert len(audit.events) == 1
    assert audit.events[0]["actor"] == "operator-test"
    assert audit.events[0]["actor"] != "attacker-controlled-actor"


@pytest.mark.asyncio
async def test_approval_api_rejects_invalid_lifecycle_transition() -> None:
    repository = FakeAsyncRepository(
        make_publication(PublicationStatus.DRAFT)
    )

    service = make_service(repository)

    app = FastAPI()
    app.include_router(
        create_announcement_operations_approval_router(
            approval_service=service,
        )
    )

    app.dependency_overrides[announcement_publish_permission] = (
        allow_announcement_publish_permission
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/announcement-operations/publications/"
            "ws23-1-3-api-test/approve",
            json={},
        )

    assert response.status_code == 409

    assert repository.publication is not None
    assert repository.publication.status is PublicationStatus.DRAFT

    assert repository.saved == []