from backend.governance.audit_event import AuditEvent


def test_audit_event_creation():
    event = AuditEvent.create(
        event="PROVIDER_PAUSED",
        actor="admin",
        reason="Incident",
        component="provider_management",
    )

    assert event.event == "PROVIDER_PAUSED"
    assert event.actor == "admin"
    assert event.timestamp is not None
