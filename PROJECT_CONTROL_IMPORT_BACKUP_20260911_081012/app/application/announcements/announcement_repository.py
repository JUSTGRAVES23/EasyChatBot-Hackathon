"""Repository port for Announcement Operations."""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.announcements.announcement import Announcement


class AnnouncementRepository(Protocol):
    async def save(self, announcement: Announcement) -> Announcement: ...
    async def get(self, announcement_id: UUID) -> Announcement | None: ...
    async def list(self) -> tuple[Announcement, ...]: ...

