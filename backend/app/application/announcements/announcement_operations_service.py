"""Application service for controlled Announcement Operations lifecycle."""
from __future__ import annotations

from uuid import UUID, uuid4

from backend.app.domain.announcements.announcement import Announcement
from backend.app.domain.announcements.publication_event import PublicationEvent, PublicationEventType
from .announcement_repository import AnnouncementRepository
from .publication_event_repository import PublicationEventRepository


class AnnouncementOperationsService:
    """Coordinates lifecycle changes and immutable audit events.

    This foundation intentionally does not deliver to Telegram. Delivery is a
    later adapter behind an explicit port so the domain remains provider-independent.
    """

    def __init__(self, *, repository: AnnouncementRepository, event_repository: PublicationEventRepository) -> None:
        self._repository = repository
        self._events = event_repository

    async def create(self, *, title: str, body: str, actor: str, correlation_id: str | None = None) -> Announcement:
        if not title.strip() or not body.strip() or not actor.strip():
            raise ValueError("title, body and actor are required.")
        announcement = Announcement(title=title.strip(), body=body.strip(), created_by=actor.strip())
        await self._repository.save(announcement)
        await self._audit(announcement, PublicationEventType.CREATED, actor, correlation_id)
        return announcement

    async def mark_ready_for_review(self, announcement_id: UUID, *, actor: str, correlation_id: str | None = None) -> Announcement:
        announcement = await self._require(announcement_id)
        announcement.mark_ready_for_review()
        await self._repository.save(announcement)
        await self._audit(announcement, PublicationEventType.READY_FOR_REVIEW, actor, correlation_id)
        return announcement

    async def approve(self, announcement_id: UUID, *, actor: str, correlation_id: str | None = None) -> Announcement:
        announcement = await self._require(announcement_id)
        announcement.approve(actor)
        await self._repository.save(announcement)
        await self._audit(announcement, PublicationEventType.APPROVED, actor, correlation_id)
        return announcement

    async def request_publication(self, announcement_id: UUID, *, actor: str, correlation_id: str | None = None) -> Announcement:
        announcement = await self._require(announcement_id)
        announcement.request_publication()
        await self._repository.save(announcement)
        await self._audit(announcement, PublicationEventType.PUBLISH_REQUESTED, actor, correlation_id)
        return announcement

    async def mark_published(self, announcement_id: UUID, *, actor: str, correlation_id: str | None = None, provider_message_id: str | None = None) -> Announcement:
        announcement = await self._require(announcement_id)
        announcement.mark_published()
        await self._repository.save(announcement)
        await self._audit(announcement, PublicationEventType.PUBLISHED, actor, correlation_id, provider_message_id=provider_message_id)
        return announcement

    async def mark_failed(self, announcement_id: UUID, *, actor: str, error_code: str, correlation_id: str | None = None) -> Announcement:
        announcement = await self._require(announcement_id)
        announcement.mark_failed()
        await self._repository.save(announcement)
        await self._audit(announcement, PublicationEventType.FAILED, actor, correlation_id, error_code=error_code)
        return announcement

    async def get(self, announcement_id: UUID) -> Announcement:
        return await self._require(announcement_id)

    async def list(self) -> tuple[Announcement, ...]:
        return await self._repository.list()

    async def audit_log(self, announcement_id: UUID) -> tuple[PublicationEvent, ...]:
        await self._require(announcement_id)
        return await self._events.list_for_publication(announcement_id)

    async def _require(self, announcement_id: UUID) -> Announcement:
        announcement = await self._repository.get(announcement_id)
        if announcement is None:
            raise LookupError(f"Announcement {announcement_id} was not found.")
        return announcement

    async def _audit(self, announcement: Announcement, event_type: PublicationEventType, actor: str, correlation_id: str | None, *, error_code: str | None = None, provider_message_id: str | None = None) -> None:
        if not actor.strip():
            raise ValueError("actor cannot be empty.")
        await self._events.append(PublicationEvent(
            publication_id=announcement.id,
            event_type=event_type,
            actor=actor,
            correlation_id=correlation_id or str(uuid4()),
            error_code=error_code,
            provider_message_id=provider_message_id,
        ))
