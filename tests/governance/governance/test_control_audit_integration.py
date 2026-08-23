from backend.governance.governance_audit_service import (
    GovernanceAuditService,
)
from backend.provider_management.control.provider_delivery_control import (
    ProviderDeliveryControl,
)


def test_provider_pause_creates_audit_event():

    audit = GovernanceAuditService()

    control = ProviderDeliveryControl(
        audit_service=audit,
    )

    control.pause(
        "Provider incident",
        actor="security_admin",
    )

    events = audit.list_events()

    assert len(events) == 1
    assert events[0].event == "PROVIDER_PAUSED"
    assert events[0].actor == "security_admin"
