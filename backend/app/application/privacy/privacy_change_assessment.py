from __future__ import annotations

from dataclasses import dataclass

from .privacy_change import PrivacyChange, PrivacyChangeRisk
from .privacy_change_detector import PrivacyChangeDetection


@dataclass(frozen=True, slots=True)
class PrivacyChangeAssessment:
    risk: PrivacyChangeRisk
    dpo_required: bool
    grc_required: bool
    dpia_screening_required: bool
    reasons: tuple[str, ...]


class PrivacyChangeAssessmentService:
    """Apply deterministic Beta 1 governance-routing rules.

    This is a routing aid, not a legal determination. DPO/GRC retain
    authority over the final governance decision.
    """

    def assess(
        self,
        change: PrivacyChange,
        detection: PrivacyChangeDetection,
    ) -> PrivacyChangeAssessment:
        if change is None:
            raise ValueError("change cannot be None.")
        if detection is None:
            raise ValueError("detection cannot be None.")

        if not detection.privacy_impacting:
            return PrivacyChangeAssessment(
                risk=PrivacyChangeRisk.LOW,
                dpo_required=False,
                grc_required=False,
                dpia_screening_required=False,
                reasons=(),
            )

        high = (
            change.data_categories_changed
            or change.processor_changed
            or change.transfer_changed
            or change.automated_decision_changed
        )
        risk = PrivacyChangeRisk.HIGH if high else PrivacyChangeRisk.MEDIUM

        return PrivacyChangeAssessment(
            risk=risk,
            dpo_required=True,
            grc_required=True,
            dpia_screening_required=high,
            reasons=detection.reasons,
        )
