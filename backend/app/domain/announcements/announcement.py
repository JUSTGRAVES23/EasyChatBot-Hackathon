"""Announcement domain aggregate."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

from .publication_status import PublicationStatus


@dataclass(slots=True)
class Announcement:
    """Official announcement and its controlled publication lifecycle."""

    title: str
    body: str
    created_by: str
    id: UUID = field(default_factory=uuid4)
    status: PublicationStatus = PublicationStatus.DRAFT
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by: str | None = None
    approved_at: datetime | None = None

    def mark_ready_for_review(self) -> None:
        self._transition(PublicationStatus.READY_FOR_REVIEW)

    def approve(self, actor: str) -> None:
        if not actor.strip():
            raise ValueError("actor cannot be empty.")
        self._transition(PublicationStatus.APPROVED)
        self.approved_by = actor
        self.approved_at = datetime.now(timezone.utc)

    def request_publication(self) -> None:
        self._transition(PublicationStatus.PUBLISH_REQUESTED)

    def mark_published(self) -> None:
        self._transition(PublicationStatus.PUBLISHED)

    def mark_failed(self) -> None:
        self._transition(PublicationStatus.FAILED)

    def archive(self) -> None:
        self._transition(PublicationStatus.ARCHIVED)

    def _transition(self, target: PublicationStatus) -> None:
        allowed = {
            PublicationStatus.DRAFT: {PublicationStatus.READY_FOR_REVIEW, PublicationStatus.ARCHIVED},
            PublicationStatus.READY_FOR_REVIEW: {PublicationStatus.DRAFT, PublicationStatus.APPROVED, PublicationStatus.ARCHIVED},
            PublicationStatus.APPROVED: {PublicationStatus.PUBLISH_REQUESTED, PublicationStatus.ARCHIVED},
            PublicationStatus.PUBLISH_REQUESTED: {PublicationStatus.PUBLISHED, PublicationStatus.FAILED},
            PublicationStatus.FAILED: {PublicationStatus.PUBLISH_REQUESTED, PublicationStatus.ARCHIVED},
            PublicationStatus.PUBLISHED: {PublicationStatus.ARCHIVED},
            PublicationStatus.ARCHIVED: set(),
        }
        if target not in allowed[self.status]:
            raise ValueError(f"Invalid publication transition: {self.status} -> {target}.")
        self.status = target
        self.updated_at = datetime.now(timezone.utc)
