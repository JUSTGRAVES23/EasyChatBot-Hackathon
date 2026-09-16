from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.domain.announcements.publication import Publication
from app.domain.announcements.template_models import PublicationStatus


class AsyncPublicationStore(Protocol):
    async def get_async(self, publication_id: str) -> Publication | None:
        ...

    async def save_async(self, publication: Publication) -> None:
        ...


class PublicationApprovalAudit(Protocol):
    async def record_approval(
        self,
        *,
        publication: Publication,
        actor: str,
        occurred_at: datetime,
    ) -> None:
        ...


@dataclass(frozen=True)
class AsyncPublicationApprovalResult:
    publication: Publication
    actor: str
    approved_at: datetime


class AsyncAnnouncementPublicationApprovalService:
    """Async PostgreSQL-backed approval application boundary.

    The domain model remains the authority for lifecycle transitions.
    This service never invokes WS-22 execution or Telegram.
    """

    def __init__(
        self,
        *,
        publications: AsyncPublicationStore,
        audit: PublicationApprovalAudit,
    ) -> None:
        if publications is None or audit is None:
            raise ValueError("publications and audit are required.")
        self._publications = publications
        self._audit = audit

    async def approve(
        self,
        *,
        publication_id: str,
        actor: str,
    ) -> AsyncPublicationApprovalResult:
        if not actor.strip():
            raise ValueError("actor cannot be empty.")

        publication = await self._publications.get_async(publication_id)
        if publication is None:
            raise LookupError(f"Unknown publication '{publication_id}'.")

        if publication.status is not PublicationStatus.PENDING_APPROVAL:
            # Use the domain transition so the canonical lifecycle error remains
            # authoritative and consistent with the existing domain model.
            publication.approve()

        else:
            publication.approve()

        approved_at = publication.approved_at or datetime.now(timezone.utc)

        await self._publications.save_async(publication)
        await self._audit.record_approval(
            publication=publication,
            actor=actor.strip(),
            occurred_at=approved_at,
        )

        return AsyncPublicationApprovalResult(
            publication=publication,
            actor=actor.strip(),
            approved_at=approved_at,
        )


__all__ = [
    "AsyncAnnouncementPublicationApprovalService",
    "AsyncPublicationApprovalResult",
]

