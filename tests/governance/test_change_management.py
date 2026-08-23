from backend.governance.change_management.change_management_service import (
    ChangeManagementService,
)


def test_change_record_creation():

    service = ChangeManagementService()

    record = service.create_change(
        approval_id="APR-001",
        component="email_provider",
        action="PAUSE_PROVIDER",
    )

    assert record.change_id == "CHG-001"
