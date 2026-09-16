from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from app.application.announcements.publication_service import (
    AnnouncementPublicationService,
)
from app.domain.announcements.publication import Publication


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
class PublicationApprovalResult:
    publication: Publication
    actor: str
    approved_at: datetime


class AnnouncementPublicationApprovalService:
    """Authorized application boundary for WS-23.1.3 approval.

    Lifecycle validation remains in the Publication domain model.
    Persistence remains behind PublicationRepository.
    Telegram delivery is deliberately outside this service.
    """

    def __init__(
        self,
        *,
        publications: AnnouncementPublicationService,
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
    ) -> PublicationApprovalResult:
        if not actor.strip():
            raise ValueError("actor cannot be empty.")

        publication = self._publications.approve(publication_id)
        approved_at = publication.approved_at or datetime.now(timezone.utc)

        await self._audit.record_approval(
            publication=publication,
            actor=actor.strip(),
            occurred_at=approved_at,
        )

        return PublicationApprovalResult(
            publication=publication,
            actor=actor.strip(),
            approved_at=approved_at,
        )

