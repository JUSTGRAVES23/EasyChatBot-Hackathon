class GovernanceTimelineViewModel:

    def build(self, entry):
        return {
            "event_id": entry.event_id,
            "event": entry.event,
            "component": entry.component,
            "actor": entry.actor,
            "reason": entry.reason,
            "severity": entry.severity,
            "evidence_available": entry.evidence_available,
            "timestamp": entry.timestamp.isoformat(),
        }

    def build_collection(self, entries):
        return [
            self.build(entry)
            for entry in entries
        ]
