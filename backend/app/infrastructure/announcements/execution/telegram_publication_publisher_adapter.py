"""
WS-23.1.4 Telegram publication adapter.

Architecture:

WS-22 AnnouncementPublisher
        ↓
TelegramPublicationPublisherAdapter
        ↓
ControlledAnnouncementPublisher
        ↓
TelegramAnnouncementPublisher
        ↓
Existing Telegram client

This adapter:
- does not create a Telegram client;
- does not implement idempotency;
- does not create a repository;
- does not create a database;
- does not bypass the controlled publisher;
- translates the provider-independent WS-22 contract into the
  existing controlled Telegram publication boundary.
"""

from __future__ import annotations

from os import getenv
from uuid import UUID

from app.application.announcement.announcement_publisher import (
    ControlledAnnouncementPublisher,
)
from app.application.announcements.execution.contracts import (
    AnnouncementPublisher,
)


class TelegramPublicationPublisherAdapter(AnnouncementPublisher):
    """Bridge the canonical WS-22 publisher contract to Telegram."""

    def __init__(
        self,
        *,
        publisher: ControlledAnnouncementPublisher,
        channel_id: str | None = None,
        announcement_type: str = "beta_update",
    ) -> None:
        if publisher is None:
            raise ValueError("publisher cannot be None.")

        resolved_channel_id = channel_id or getenv(
            "BETA1_ANNOUNCEMENT_CHANNEL_ID"
        )

        if not resolved_channel_id or not resolved_channel_id.strip():
            raise ValueError(
                "BETA1_ANNOUNCEMENT_CHANNEL_ID is not configured."
            )

        if not announcement_type.strip():
            raise ValueError(
                "announcement_type cannot be empty."
            )

        self._publisher = publisher
        self._channel_id = resolved_channel_id.strip()
        self._announcement_type = announcement_type.strip()

    async def publish(
        self,
        *,
        publication_id: UUID,
        title: str,
        content: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> str | None:
        """
        Publish through the existing controlled Telegram boundary.

        WS-22 remains responsible for:
        - idempotency;
        - execution persistence;
        - execution audit;
        - retry semantics.

        This adapter only translates the publication request.
        """

        if not isinstance(publication_id, UUID):
            raise ValueError(
                "publication_id must be a UUID."
            )

        if not title.strip():
            raise ValueError(
                "title cannot be empty."
            )

        if not content.strip():
            raise ValueError(
                "content cannot be empty."
            )

        if not correlation_id.strip():
            raise ValueError(
                "correlation_id cannot be empty."
            )

        if not idempotency_key.strip():
            raise ValueError(
                "idempotency_key cannot be empty."
            )

        text = (
            f"*{title.strip()}*\n\n"
            f"{content.strip()}"
        )

        record = await self._publisher.publish(
            channel_id=self._channel_id,
            text=text,
            announcement_type=self._announcement_type,
        )

        return record.message_id


__all__ = [
    "TelegramPublicationPublisherAdapter",
]
