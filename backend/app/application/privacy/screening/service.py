from __future__ import annotations

from uuid import uuid4

from .models import AssessmentOutcome, ScreeningCriterion, ScreeningResult


class ScreeningService:
    """M3 screening/applicability execution seam.

    Final DPO/legal decisions remain outside this service. Unknown legally
    material inputs fail closed.
    """

    def screen(
        self,
        *,
        processing_id: str,
        criteria: tuple[ScreeningCriterion, ...],
        legal_materiality_established: bool,
        material_change_detected: bool,
    ) -> ScreeningResult:
        screening_id = f"SCR-{uuid4().hex[:12].upper()}"

        if not legal_materiality_established:
            return ScreeningResult(
                screening_id=screening_id,
                processing_id=processing_id,
                status="LEGAL_REVIEW_REQUIRED",
                outcomes=(
                    {
                        "assessment": "DPIA",
                        "outcome": AssessmentOutcome.LEGAL_REVIEW_REQUIRED,
                        "matched_criteria": [],
                        "rationale": "Legally material screening input cannot be established.",
                    },
                    {
                        "assessment": "FRIA",
                        "outcome": AssessmentOutcome.LEGAL_REVIEW_REQUIRED,
                        "matched_criteria": [],
                        "rationale": "Fundamental-rights applicability requires human/legal determination.",
                    },
                    {
                        "assessment": "TIA",
                        "outcome": AssessmentOutcome.LEGAL_REVIEW_REQUIRED,
                        "matched_criteria": [],
                        "rationale": "Transfer applicability requires approved methodology and transfer context.",
                    },
                ),
                reassessment_required=material_change_detected,
                provenance=criteria,
                rationale="Human DPO/legal review is required before applicability can be concluded.",
            )

        matched = tuple(item for item in criteria if item.satisfied)
        return ScreeningResult(
            screening_id=screening_id,
            processing_id=processing_id,
            status="COMPLETED",
            outcomes=(
                {
                    "assessment": "DPIA",
                    "outcome": AssessmentOutcome.REQUIRED if matched else AssessmentOutcome.NOT_REQUIRED,
                    "matched_criteria": list(matched),
                    "rationale": (
                        "At least one configured governed criterion is satisfied."
                        if matched
                        else "No configured governed criterion is satisfied."
                    ),
                },
            ),
            reassessment_required=material_change_detected,
            provenance=criteria,
            rationale="Screening completed from governed processing context.",
        )


__all__ = ["ScreeningService"]
