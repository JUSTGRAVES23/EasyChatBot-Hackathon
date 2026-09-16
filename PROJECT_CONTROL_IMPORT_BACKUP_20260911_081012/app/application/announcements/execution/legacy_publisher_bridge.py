"""WS-22.3.3.x legacy publisher migration bridge.

This module provides the explicit migration boundary between the existing
Beta announcement publisher contract and the canonical WS-22 execution
publisher contract.

The bridge is intentionally provider-independent. It does not know about
Telegram, HTTP, credentials, or external SDKs.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.application.announcements.execution.contracts import (
    AnnouncementPublisher,
)


class LegacyAnnouncementPublisher(Protocol):
    """Existing Beta publisher contract.

    This protocol mirrors the legacy application boundary that is still used
    by the existing ControlledAnnouncementPublisher path.

    It is intentionally isolated here as a migration dependency and must not
    be used by the new WS-22 execution service.
    """

    async def publish(
        self,
        *,
        channel_id: str,
        text: str,
    ) -> str:
        """Publish using the existing legacy publication boundary."""


class LegacyAnnouncementPublisherBridge(AnnouncementPublisher):
    """Adapt the existing publisher to the canonical WS-22 port.

    The bridge is the temporary migration boundary between:

        WS-22 execution contract
                    â†“
        legacy announcement publisher
                    â†“
        existing provider adapter

    No provider-specific behaviour belongs here.

    The channel identifier is configuration supplied by the composition root.
    It is deliberately not persisted or invented by the execution service.
    """

    def __init__(
        self,
        *,
        publisher: LegacyAnnouncementPublisher,
        channel_id: str,
    ) -> None:
        if publisher is None:
            raise ValueError("publisher cannot be None.")

        if not channel_id.strip():
            raise ValueError("channel_id cannot be empty.")

        self._publisher = publisher
        self._channel_id = channel_id

    async def publish(
        self,
        *,
        publication_id: UUID,
        title: str,
        content: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> str | None:
        """Publish through the existing legacy publisher.

        WS-22 execution metadata is deliberately not passed to the legacy
        publisher because that older contract does not support it.

        Idempotency and correlation remain owned by the WS-22 execution
        service and durable execution repository.
        """

        del publication_id
        del correlation_id
        del idempotency_key

        text = self._compose_message(
            title=title,
            content=content,
        )

        return await self._publisher.publish(
            channel_id=self._channel_id,
            text=text,
        )

    @staticmethod
    def _compose_message(
        *,
        title: str,
        content: str,
    ) -> str:
        normalized_title = title.strip()
        normalized_content = content.strip()

        if not normalized_title:
            raise ValueError("title cannot be empty.")

        if not normalized_content:
            raise ValueError("content cannot be empty.")

        return f"{normalized_title}\n\n{normalized_content}"


__all__ = [
    "LegacyAnnouncementPublisher",
    "LegacyAnnouncementPublisherBridge",
]
