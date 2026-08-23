"""
Governance Audit Event.

Represents immutable governance evidence generated
by control actions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class AuditEvent:
    event: str
    actor: str
    reason: str
    component: str
    timestamp: datetime

    @classmethod
    def create(
        cls,
        *,
        event: str,
        actor: str,
        reason: str,
        component: str,
    ) -> "AuditEvent":
        return cls(
            event=event,
            actor=actor,
            reason=reason,
            component=component,
            timestamp=datetime.now(UTC),
        )
