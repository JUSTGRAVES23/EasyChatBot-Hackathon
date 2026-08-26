from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class AnnouncementAuditEventType(str, Enum):
    CREATED = "created"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVED = "approved"
    PUBLISH_STARTED = "publish_started"
    PUBLISHED = "published"
    PUBLISH_FAILED = "publish_failed"


@dataclass(frozen=True)
class AnnouncementAuditEvent:
    publication_id: str
    event_type: AnnouncementAuditEventType
    occurred_at: datetime
    details: str | None = None


class InMemoryAnnouncementAuditSink:
    def __init__(self) -> None:
        self._events: list[AnnouncementAuditEvent] = []

    def record(
        self,
        publication_id: str,
        event_type: AnnouncementAuditEventType,
        details: str | None = None,
    ) -> AnnouncementAuditEvent:
        event = AnnouncementAuditEvent(
            publication_id=publication_id,
            event_type=event_type,
            occurred_at=datetime.now(timezone.utc),
            details=details,
        )
        self._events.append(event)
        return event

    def list_for(self, publication_id: str) -> tuple[AnnouncementAuditEvent, ...]:
        return tuple(e for e in self._events if e.publication_id == publication_id)
