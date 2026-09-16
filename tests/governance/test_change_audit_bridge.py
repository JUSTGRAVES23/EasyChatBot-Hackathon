from governance.change_management.change_audit_bridge import (
    ChangeAuditBridge,
)


class FakeAudit:

    def __init__(self):
        self.events = []

    def record(self, **kwargs):
        self.events.append(kwargs)
        return kwargs


def test_change_audit_bridge():

    audit = FakeAudit()
    bridge = ChangeAuditBridge(audit)

    class FakeChange:
        change_id = "CHG-001"
        component = "provider"
        reason = "incident"

        class change_type:
            value = "PROVIDER"

        class risk:
            value = "CRITICAL"

        class status:
            value = "APPROVED"

    result = bridge.record_change_event(
        "CHANGE_APPROVED",
        FakeChange(),
        "admin",
    )

    assert result["event"] == "CHANGE_APPROVED"
    assert len(audit.events) == 1

