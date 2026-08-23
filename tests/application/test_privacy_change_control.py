from backend.app.application.privacy.privacy_change import (
    PrivacyChange,
    PrivacyChangeRisk,
    PrivacyChangeStatus,
)
from backend.app.application.privacy.privacy_change_detector import (
    PrivacyChangeDetector,
)
from backend.app.application.privacy.privacy_change_assessment import (
    PrivacyChangeAssessmentService,
)
from backend.app.application.privacy.privacy_change_registry import (
    PrivacyChangeRegistry,
)
from backend.app.application.privacy.privacy_governance_gate import (
    PrivacyGovernanceGate,
)


def make_change(**kwargs):
    return PrivacyChange(
        change_id="PCR-001",
        title="Add analytics",
        description="Add learning analytics processing.",
        **kwargs,
    )


def test_detector_identifies_new_processing():
    result = PrivacyChangeDetector().detect(
        {"new_processing_activity": True}
    )
    assert result.privacy_impacting is True
    assert "new processing activity" in result.reasons


def test_detector_allows_non_privacy_technical_change():
    result = PrivacyChangeDetector().detect(
        {"code_refactor_only": True}
    )
    assert result.privacy_impacting is False


def test_assessment_routes_material_change_to_dpo_and_grc():
    change = make_change(purpose_changed=True)
    detection = PrivacyChangeDetector().detect(
        {"purpose_changed": True}
    )
    assessment = PrivacyChangeAssessmentService().assess(change, detection)
    assert assessment.risk == PrivacyChangeRisk.MEDIUM
    assert assessment.dpo_required is True
    assert assessment.grc_required is True
    assert assessment.dpia_screening_required is False


def test_high_risk_change_requires_dpia_screening():
    change = make_change(
        processor_changed=True,
        transfer_changed=True,
    )
    detection = PrivacyChangeDetector().detect(
        {
            "processor_changed": True,
            "transfer_changed": True,
        }
    )
    assessment = PrivacyChangeAssessmentService().assess(change, detection)
    assert assessment.risk == PrivacyChangeRisk.HIGH
    assert assessment.dpia_screening_required is True


def test_gate_blocks_until_dpo_and_grc_approve():
    registry = PrivacyChangeRegistry()
    gate = PrivacyGovernanceGate(registry=registry)
    change = make_change(
        purpose_changed=True,
        dpo_required=True,
        grc_required=True,
    )

    pending = gate.route(
        change,
        automated_validation_passed=True,
    )
    assert pending.status == PrivacyChangeStatus.PENDING_DPO_GRC
    assert gate.can_proceed("PCR-001") is False

    approved = gate.route(
        pending,
        automated_validation_passed=True,
        dpo_approved=True,
        grc_approved=True,
    )
    assert approved.status == PrivacyChangeStatus.APPROVED
    assert gate.can_proceed("PCR-001") is True


def test_gate_blocks_failed_automated_validation():
    registry = PrivacyChangeRegistry()
    gate = PrivacyGovernanceGate(registry=registry)
    change = make_change()

    blocked = gate.route(
        change,
        automated_validation_passed=False,
    )
    assert blocked.status == PrivacyChangeStatus.BLOCKED
    assert gate.can_proceed("PCR-001") is False
