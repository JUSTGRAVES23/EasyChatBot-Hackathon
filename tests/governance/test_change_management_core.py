from backend.governance.change_management.change_management_service import (
    ChangeManagementService,
)
from backend.governance.change_management.change_risk import ChangeRisk
from backend.governance.change_management.change_status import ChangeStatus
from backend.governance.change_management.change_type import ChangeType


def test_provider_change_is_created_pending_approval():

    service = ChangeManagementService()

    record = service.create_change(
        component="openai",
        action="PAUSE_PROVIDER",
        reason="Provider incident",
        requested_by="admin",
        change_type=ChangeType.PROVIDER,
        risk=ChangeRisk.CRITICAL,
        approval_id="APR-001",
    )

    assert record.change_id == "CHG-001"
    assert record.change_type == ChangeType.PROVIDER
    assert record.risk == ChangeRisk.CRITICAL
    assert record.status == ChangeStatus.PENDING_APPROVAL


def test_model_change_is_supported():

    service = ChangeManagementService()

    record = service.create_change(
        component="gpt-5-mini",
        action="CHANGE_MODEL_CONFIGURATION",
        reason="Performance improvement",
        requested_by="admin",
        change_type=ChangeType.MODEL,
        risk=ChangeRisk.HIGH,
    )

    assert record.change_type == ChangeType.MODEL
    assert record.status == ChangeStatus.PROPOSED


def test_change_lifecycle_is_explicit():

    service = ChangeManagementService()

    record = service.create_change(
        component="scheduler",
        action="CHANGE_SCHEDULE",
        reason="Maintenance window",
        requested_by="admin",
        change_type=ChangeType.SCHEDULER,
        risk=ChangeRisk.MEDIUM,
    )

    record = service.mark_approved(record.change_id)
    assert record.status == ChangeStatus.APPROVED

    record = service.mark_scheduled(record.change_id)
    assert record.status == ChangeStatus.SCHEDULED

    record = service.mark_executed(record.change_id)
    assert record.status == ChangeStatus.EXECUTED


def test_change_management_does_not_execute_controls():

    service = ChangeManagementService()

    record = service.create_change(
        component="email_provider",
        action="PAUSE_PROVIDER",
        reason="Incident",
        requested_by="admin",
        change_type=ChangeType.PROVIDER,
        risk=ChangeRisk.CRITICAL,
    )

    assert record.status == ChangeStatus.PROPOSED
    assert not hasattr(service, "execute")
    assert not hasattr(service, "pause_provider")
