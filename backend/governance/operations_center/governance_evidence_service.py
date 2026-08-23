from __future__ import annotations


class GovernanceEvidenceService:
    '''
    Read-only governance evidence projection.
    '''

    def __init__(
        self,
        audit_service=None,
    ):
        self.audit_service = audit_service


    def timeline(self) -> list[dict]:

        if not self.audit_service:
            return []

        return [
            {
                "event": event.event,
                "actor": event.actor,
                "reason": event.reason,
                "component": event.component,
                "timestamp": event.timestamp.isoformat(),
            }
            for event in self.audit_service.list_events()
        ]
