from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.application.privacy.processing_registry import ProcessingRegistry
from app.application.privacy.screening.adapter import ProcessingActivityScreeningAdapter


class ScreeningRequest(BaseModel):
    """Production screening command. Only processing_id is client-controlled."""

    processing_id: str = Field(min_length=1)


def create_privacy_screening_router(
    *,
    processing_registry: ProcessingRegistry,
    screening_adapter: ProcessingActivityScreeningAdapter,
) -> APIRouter:
    router = APIRouter(
        prefix="/api/privacy/screening",
        tags=["privacy-screening"],
    )

    @router.get("/processing-activities")
    def list_processing_activities() -> list[dict[str, Any]]:
        return [
            {
                "processing_id": activity.processing_id,
                "name": activity.name,
                "purpose": activity.purpose,
                "data_subjects": list(activity.data_subjects),
                "data_categories": list(activity.data_categories),
                "special_category_data": bool(
                    activity.metadata.get("special_category_data", False)
                ),
                "processor_ids": list(activity.processor_ids),
                "transfer_status": activity.metadata.get("transfer_status"),
                "last_material_change_at": activity.metadata.get(
                    "last_material_change_at"
                ),
            }
            for activity in processing_registry.all()
        ]

    @router.post("/screen")
    def screen(request: ScreeningRequest) -> dict[str, Any]:
        try:
            activity = processing_registry.get(request.processing_id)
        except KeyError as exc:
            raise HTTPException(
                status_code=404,
                detail="Processing activity not found.",
            ) from exc

        result = screening_adapter.screen(activity)

        def criterion_payload(criterion: Any) -> dict[str, Any]:
            return {
                "code": criterion.code,
                "label": criterion.label,
                "satisfied": criterion.satisfied,
                "source": criterion.source,
                "source_version": criterion.source_version,
                "rationale": criterion.rationale,
            }

        return {
            "screening_id": result.screening_id,
            "processing_id": result.processing_id,
            "status": result.status,
            "outcomes": [
                {
                    "assessment": outcome["assessment"],
                    "outcome": str(outcome["outcome"]),
                    "matched_criteria": [
                        criterion_payload(c)
                        for c in outcome.get("matched_criteria", [])
                    ],
                    "rationale": outcome["rationale"],
                }
                for outcome in result.outcomes
            ],
            "reassessment_required": result.reassessment_required,
            "provenance": [
                criterion_payload(c) for c in result.provenance
            ],
            "rationale": result.rationale,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    return router


__all__ = ["ScreeningRequest", "create_privacy_screening_router"]


