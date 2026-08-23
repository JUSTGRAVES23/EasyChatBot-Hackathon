from backend.governance.change_management.change_management_service import (
    ChangeManagementService,
)
from backend.governance.change_management.change_type import ChangeType
from backend.governance.change_management.change_risk import ChangeRisk
from backend.governance.approval.approval_change_service import (
    ApprovalChangeService,
)


def test_approval_changes_lifecycle():

    service = ChangeManagementService()

    record = service.create_change(
        component="openai",
        action="PAUSE_PROVIDER",
        reason="Provider incident",
        requested_by="admin",
        change_type=ChangeType.PROVIDER,
        risk=ChangeRisk.CRITICAL,
    )

    approval = ApprovalChangeService(
        change_service=service,
    )

    result = approval.approve_change(
        record.change_id,
        "admin",
    )

    assert result.status.value == "APPROVED"
