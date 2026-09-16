from __future__ import annotations

"""Adapter between authoritative ProcessingActivity data and M3 screening."""

from ..processing_activity import ProcessingActivity
from .models import ScreeningCriterion, ScreeningResult
from .service import ScreeningService


class ProcessingActivityScreeningAdapter:
    """Derive governed screening input and invoke the existing M3 seam.

    The browser never supplies screening criteria or legal-materiality
    assertions. Missing legally material information fails closed.
    """

    def __init__(self, screening_service: ScreeningService | None = None) -> None:
        self._screening_service = screening_service or ScreeningService()

    def screen(self, activity: ProcessingActivity) -> ScreeningResult:
        metadata = activity.metadata

        criteria = (
            ScreeningCriterion(
                code="SPECIAL_CATEGORY_DATA",
                label="Special-category data is explicitly recorded",
                satisfied=bool(metadata.get("special_category_data", False)),
                source="ProcessingActivity.metadata",
                source_version="beta1-processing-catalog-v1",
                rationale="Derived from the controlled Processing Activity record.",
            ),
            ScreeningCriterion(
                code="EXTERNAL_DESTINATION",
                label="External destination is recorded",
                satisfied=bool(activity.destinations),
                source="ProcessingActivity",
                source_version="beta1-processing-catalog-v1",
                rationale="Derived from authoritative processing destinations.",
            ),
            ScreeningCriterion(
                code="LEGAL_BASIS_PENDING",
                label="Lawful basis is not yet finally established",
                satisfied=activity.legal_basis.startswith("PENDING_"),
                source="ProcessingActivity",
                source_version="beta1-processing-catalog-v1",
                rationale="A pending lawful-basis value prevents final applicability.",
            ),
        )

        return self._screening_service.screen(
            processing_id=activity.processing_id,
            criteria=criteria,
            legal_materiality_established=bool(
                metadata.get("legal_materiality_established", False)
            ),
            material_change_detected=bool(
                metadata.get("material_change_detected", False)
            ),
        )


__all__ = ["ProcessingActivityScreeningAdapter"]
