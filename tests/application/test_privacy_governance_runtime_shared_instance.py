from __future__ import annotations

from app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from app.application.privacy.privacy_governance_composition import (
    get_privacy_governance_composition,
    reset_privacy_governance_composition_for_tests,
)
from app.application.privacy.privacy_governance_runtime import (
    process_new_processing_governance,
)


def test_runtime_bridge_writes_to_the_same_composition_seen_by_dashboard():
    reset_privacy_governance_composition_for_tests()

    try:
        composition = get_privacy_governance_composition()

        change = PrivacyChange(
            change_id="PCR-RUNTIME-001",
            title="Runtime integration test",
            description="A real privacy governance event.",
            risk=PrivacyChangeRisk.MEDIUM,
            status=PrivacyChangeStatus.PENDING_DPO_GRC,
            dpo_required=True,
            grc_required=True,
        )

        result = process_new_processing_governance(
            change,
            automated_validation_passed=True,
        )

        assert result.case.case_id == "CASE-PCR-RUNTIME-001"
        assert composition.case_registry.get(
            "CASE-PCR-RUNTIME-001"
        ) is result.case

        assert composition.dashboard_service.summary() == {
            "total_cases": 1,
            "pending": 1,
            "approved": 0,
            "blocked": 0,
            "approval_records": 0,
        }
    finally:
        reset_privacy_governance_composition_for_tests()

