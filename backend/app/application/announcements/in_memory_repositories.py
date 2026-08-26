"""Small deterministic repositories for tests and local foundation work."""
from __future__ import annotations

from uuid import UUID

from backend.app.domain.announcements.announcement import Announcement
from backend.app.domain.announcements.publication_event import PublicationEvent


class InMemoryAnnouncementRepository:
    def __init__(self) -> None:
        self._items: dict[UUID, Announcement] = {}

    async def save(self, announcement: Announcement) -> Announcement:
        self._items[announcement.id] = announcement
        return announcement

    async def get(self, announcement_id: UUID) -> Announcement | None:
        return self._items.get(announcement_id)

    async def list(self) -> tuple[Announcement, ...]:
        return tuple(self._items.values())


class InMemoryPublicationEventRepository:
    def __init__(self) -> None:
        self._events: list[PublicationEvent] = []

    async def append(self, event: PublicationEvent) -> PublicationEvent:
        self._events.append(event)
        return event

    async def list_for_publication(self, publication_id: UUID) -> tuple[PublicationEvent, ...]:
        return tuple(e for e in self._events if e.publication_id == publication_id)
