"""Immutable audit events for Announcement Operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import UUID, uuid4


class PublicationEventType(StrEnum):
    CREATED = "publication_created"
    READY_FOR_REVIEW = "publication_ready_for_review"
    APPROVED = "publication_approved"
    PUBLISH_REQUESTED = "publication_publish_requested"
    PUBLISHED = "publication_published"
    FAILED = "publication_failed"
    RETRY_REQUESTED = "publication_retry_requested"
    ARCHIVED = "publication_archived"


@dataclass(frozen=True, slots=True)
class PublicationEvent:
    publication_id: UUID
    event_type: PublicationEventType
    actor: str
    correlation_id: str
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error_code: str | None = None
    provider_message_id: str | None = None
