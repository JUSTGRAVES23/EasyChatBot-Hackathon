"""
Governance Audit Service.

Central governance evidence collection boundary.

The service is intentionally provider-independent and
side-effect free apart from its in-memory audit store.
"""

from __future__ import annotations

from backend.governance.audit_event import AuditEvent


class GovernanceAuditService:

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def record(
        self,
        *,
        event: str,
        actor: str,
        reason: str,
        component: str,
    ) -> AuditEvent:

        audit_event = AuditEvent.create(
            event=event,
            actor=actor,
            reason=reason,
            component=component,
        )

        self._events.append(audit_event)

        return audit_event

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)
