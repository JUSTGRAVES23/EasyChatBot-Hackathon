from app.application.privacy.processing_activity import ProcessingActivity
from app.application.privacy.screening.adapter import ProcessingActivityScreeningAdapter
from app.application.privacy.screening.service import ScreeningService


def test_adapter_invokes_existing_screening_service() -> None:
    activity = ProcessingActivity(
        processing_id="PA-TEST-001",
        name="Test processing",
        purpose="Test purpose",
        data_categories=("identity",),
        data_subjects=("learners",),
        source=("application",),
        destinations=("provider",),
        legal_basis="PENDING_DPO_LEGAL",
        retention_id="PENDING_DPO_GRC",
        metadata={
            "legal_materiality_established": False,
            "material_change_detected": False,
        },
    )

    result = ProcessingActivityScreeningAdapter(
        ScreeningService()
    ).screen(activity)

    assert result.processing_id == "PA-TEST-001"
    assert result.status == "LEGAL_REVIEW_REQUIRED"
    assert len(result.outcomes) == 3


def test_m3_fails_closed_when_materiality_is_unknown() -> None:
    result = ScreeningService().screen(
        processing_id="PA-TEST-002",
        criteria=(),
        legal_materiality_established=False,
        material_change_detected=False,
    )
    assert result.status == "LEGAL_REVIEW_REQUIRED"
    assert all(
        outcome["outcome"] == "LEGAL_REVIEW_REQUIRED"
        for outcome in result.outcomes
    )
