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
        """Publish text and return the Telegram message identifier."""


@dataclass(frozen=True)
class PublicationRecord:
    channel_id: str
    message_id: str
    published_at: datetime
    announcement_type: str


class PublicationDisabledError(RuntimeError):
    """Raised when publication is disabled by configuration."""


class ControlledAnnouncementPublisher:
    """Application service enforcing the Beta 1 publication kill switch."""

    def __init__(
        self,
        *,
        publisher: AnnouncementPublisher,
        publishing_enabled: bool,
    ) -> None:
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
            published_at=datetime.now(timezone.utc),
            announcement_type=announcement_type,
        )
