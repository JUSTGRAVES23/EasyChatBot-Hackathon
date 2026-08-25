from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


class AnnouncementPublisher(Protocol):
    async def publish(
        self,
        *,
        channel_id: str,
        text: str,
    ) -> str:
        """Publish an announcement and return its external message ID."""


class PublicationDisabledError(RuntimeError):
    """Raised when controlled announcement publishing is disabled."""


@dataclass(frozen=True)
class PublicationRecord:
    channel_id: str
    message_id: str
    announcement_type: str
    published_at: datetime


class ControlledAnnouncementPublisher:
    """Application boundary enforcing the explicit Beta 1 publication switch."""

    def __init__(
        self,
        *,
        publisher: AnnouncementPublisher,
        publishing_enabled: bool,
    ) -> None:
        if publisher is None:
            raise ValueError("publisher cannot be None.")

        self._publisher = publisher
        self._publishing_enabled = publishing_enabled

    async def publish(
        self,
        *,
        channel_id: str,
        text: str,
        announcement_type: str,
    ) -> PublicationRecord:
        if not self._publishing_enabled:
            raise PublicationDisabledError(
                "Telegram announcement publishing is disabled."
            )

        message_id = await self._publisher.publish(
            channel_id=channel_id,
            text=text,
        )

        return PublicationRecord(
            channel_id=channel_id,
            message_id=message_id,
            announcement_type=announcement_type,
            published_at=datetime.now(timezone.utc),
        )
