"""WS-22.3.4 execution audit adapters.

WS-22.3.4.1:
    PublicationExecutionAuditAdapter
    Bridges the execution audit contract to the existing in-memory
    announcement audit vocabulary.

WS-22.3.4.2:
    DurablePublicationExecutionAudit
    Bridges the same execution contract to the durable audit repository.

Both implementations intentionally share the same execution-facing
contract. They differ only in persistence destination.
"""

from __future__ import annotations

from uuid import UUID

from app.application.announcements.audit import (
    AnnouncementAuditEventType,
    InMemoryAnnouncementAuditSink,
)


class PublicationExecutionAuditAdapter:
    """WS-22.3.4.1 adapter for the existing announcement audit sink."""

    def __init__(
        self,
        *,
        sink: InMemoryAnnouncementAuditSink,
    ) -> None:
        if sink is None:
            raise ValueError("sink cannot be None.")

        self._sink = sink

    async def record_success(
        self,
        *,
        publication_id: UUID,
        actor: str,
        correlation_id: str,
        provider_message_id: str | None,
    ) -> None:
        self._sink.record(
            publication_id=str(publication_id),
            event_type=AnnouncementAuditEventType.PUBLISHED,
            details=(
                f"actor={actor};"
                f"correlation_id={correlation_id};"
                f"provider_message_id={provider_message_id}"
            ),
        )

    async def record_failure(
        self,
        *,
        publication_id: UUID,
        actor: str,
        correlation_id: str,
        error_code: str,
    ) -> None:
        self._sink.record(
            publication_id=str(publication_id),
            event_type=AnnouncementAuditEventType.PUBLISH_FAILED,
            details=(
                f"actor={actor};"
                f"correlation_id={correlation_id};"
                f"error_code={error_code}"
            ),
        )


class DurablePublicationExecutionAudit:
    """WS-22.3.4.2 adapter for the durable audit repository."""

    def __init__(self, *, repository) -> None:
        if repository is None:
            raise ValueError("repository cannot be None.")

        self._repository = repository

    async def record_success(
        self,
        *,
        publication_id: UUID,
        actor: str,
        correlation_id: str,
        provider_message_id: str | None,
    ) -> None:
        await self._repository.record_success(
            publication_id=publication_id,
            actor=actor,
            correlation_id=correlation_id,
            provider_message_id=provider_message_id,
        )

    async def record_failure(
        self,
        *,
        publication_id: UUID,
        actor: str,
        correlation_id: str,
        error_code: str,
    ) -> None:
        await self._repository.record_failure(
            publication_id=publication_id,
            actor=actor,
            correlation_id=correlation_id,
            error_code=error_code,
        )


__all__ = [
    "DurablePublicationExecutionAudit",
    "PublicationExecutionAuditAdapter",
]
