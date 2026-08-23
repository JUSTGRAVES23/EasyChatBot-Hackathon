class ChangeAuditBridge:
    """Connects change lifecycle events with governance evidence."""

    def __init__(self, audit_service):
        self.audit_service = audit_service

    def record_change_event(self, event, change_record, actor):
        return self.audit_service.record(
            event=event,
            actor=actor,
            reason=change_record.reason,
            component=change_record.component,
            metadata={
                "change_id": change_record.change_id,
                "change_type": change_record.change_type.value,
                "risk": change_record.risk.value,
                "status": change_record.status.value,
            },
        )
