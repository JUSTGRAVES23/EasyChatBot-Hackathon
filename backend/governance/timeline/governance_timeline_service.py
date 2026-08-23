from .governance_timeline_entry import GovernanceTimelineEntry


class GovernanceTimelineService:
    """
    Read-only governance evidence timeline.

    Does NOT:
    - execute controls;
    - approve changes;
    - modify audit records.
    """

    def __init__(self, audit_store=None):
        self.entries = []
        self.audit_store = audit_store

    def add_event(
        self,
        *,
        event: str,
        component: str,
        actor: str,
        reason: str,
        severity: str,
        evidence_available: bool = True,
    ):
        entry = GovernanceTimelineEntry(
            event_id=f"EVT-{len(self.entries)+1:03d}",
            event=event,
            component=component,
            actor=actor,
            reason=reason,
            severity=severity,
            evidence_available=evidence_available,
        )

        self.entries.append(entry)

        return entry

    def list_events(self):
        return list(self.entries)

    def latest_events(self, limit: int = 10):
        return self.entries[-limit:]
