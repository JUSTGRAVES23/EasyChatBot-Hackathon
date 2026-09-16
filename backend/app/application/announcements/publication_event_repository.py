"""Audit-event repository port."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.announcements.publication_event import PublicationEvent


class PublicationEventRepository(Protocol):
    async def append(self, event: PublicationEvent) -> PublicationEvent: ...
    async def list_for_publication(self, publication_id: UUID) -> tuple[PublicationEvent, ...]: ...

