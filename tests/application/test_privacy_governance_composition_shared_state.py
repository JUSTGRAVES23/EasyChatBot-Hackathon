from __future__ import annotations

from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from app.application.privacy.privacy_governance_composition import (
    create_privacy_governance_composition,
)


def test_all_governance_application_services_share_the_same_registries():
    composition = create_privacy_governance_composition()

    assert composition.governance_gate._registry is composition.change_registry
    assert composition.case_service._cases is composition.case_registry
    assert composition.case_service._changes is composition.change_registry
    assert composition.case_service._approvals is composition.approval_registry
    assert composition.dashboard_service._cases is composition.case_registry
    assert composition.dashboard_service._approvals is composition.approval_registry
    assert composition.flow_service._changes is composition.change_registry
    assert composition.flow_service._gate is composition.governance_gate
    assert composition.flow_service._cases is composition.case_service


def test_shared_flow_state_is_visible_without_recreating_the_composition():
    composition = create_privacy_governance_composition()

    change = PrivacyChange(
        change_id="PCR-SHARED-001",
        title="Shared state test",
        description="Shared registry integration test.",
        risk=PrivacyChangeRisk.LOW,
        status=PrivacyChangeStatus.PENDING_DPO_GRC,
        dpo_required=True,
        grc_required=True,
    )

    result = composition.flow_service.process_new_processing(
        change,
        automated_validation_passed=True,
    )

    assert composition.case_service.get_case(
        result.case.case_id
    ) is composition.case_registry.get(
        result.case.case_id
    )

    assert composition.dashboard_service.case_list()[0]["case_id"] == result.case.case_id

