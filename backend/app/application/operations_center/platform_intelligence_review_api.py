"""Application service for Platform Intelligence human-review visibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.application.operations_center.platform_intelligence_review_source import (
    PlatformIntelligenceReviewSource,
)


class PlatformIntelligenceReviewNotConfigured(RuntimeError):
    """Raised when the canonical PI review source is not configured."""


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceReviewAPI:
    """Read-only application boundary for PI review projections."""

    source: PlatformIntelligenceReviewSource | None = None

    @property
    def configured(self) -> bool:
        return self.source is not None

    def _require_source(self) -> PlatformIntelligenceReviewSource:
        if self.source is None:
            raise PlatformIntelligenceReviewNotConfigured(
                "Platform Intelligence review source is not configured."
            )

        return self.source

    def list_reviews(self) -> dict[str, Any]:
        source = self._require_source()

        items = [
            self._serialize_projection(item)
            for item in source.list_reviews()
        ]

        return {
            "status": "ready",
            "count": len(items),
            "items": items,
        }

    def get_review(self, review_item_id: str) -> dict[str, Any] | None:
        if not review_item_id or not review_item_id.strip():
            raise ValueError("review_item_id must not be blank.")

        source = self._require_source()
        item = source.get_review(review_item_id)

        if item is None:
            return None

        return self._serialize_projection(item)

    def list_escalations(self) -> dict[str, Any]:
        source = self._require_source()

        items = [
            self._serialize_projection(item)
            for item in source.list_escalations()
        ]

        recommended = [
            item
            for item in items
            if item.get("recommendation_status") == "RECOMMENDED"
        ]

        return {
            "status": "ready",
            "count": len(recommended),
            "items": recommended,
        }

    @staticmethod
    def _serialize_projection(item: Any) -> dict[str, Any]:
        """Expose only the approved PI review projection fields."""

        def value(attribute: str) -> Any:
            result = getattr(item, attribute, None)

            if hasattr(result, "value"):
                return result.value

            return result

        created_at = getattr(item, "created_at", None)
        assigned_at = getattr(item, "assigned_at", None)
        review_due_at = getattr(item, "review_due_at", None)

        return {
            "review_item_id": value("review_item_id"),
            "risk_decision_id": value("risk_decision_id"),
            "risk_assessment_id": value("risk_assessment_id"),
            "scope": value("scope"),
            "risk_level": value("risk_level"),
            "risk_score": value("risk_score"),
            "priority": value("priority"),
            "review_status": value("review_status"),
            "decision_status": value("decision_status"),
            "quality_gate_status": value("quality_gate_status"),
            "evidence_references": tuple(
                value("evidence_references") or ()
            ),
            "historical_references": tuple(
                value("historical_references") or ()
            ),
            "policy_id": value("policy_id"),
            "policy_version": value("policy_version"),
            "created_at": (
                created_at.isoformat()
                if created_at is not None
                else None
            ),
            "assigned_reviewer": value("assigned_reviewer"),
            "assigned_at": (
                assigned_at.isoformat()
                if assigned_at is not None
                else None
            ),
            "review_due_at": (
                review_due_at.isoformat()
                if review_due_at is not None
                else None
            ),
            "rationale": value("rationale"),
            "recommendation_status": value("recommendation_status"),
            "recommendation_route": value("recommendation_route"),
            "recommendation_reasons": tuple(
                value("recommendation_reasons") or ()
            ),
            "recommendation_id": value("recommendation_id"),
        }

    def __all_projection_fields(self) -> tuple[str, ...]:
        """Private marker preventing accidental metadata expansion."""
        return ()


def create_platform_intelligence_review_api(
    source: PlatformIntelligenceReviewSource | None = None,
) -> PlatformIntelligenceReviewAPI:
    """Create the governed PI review application boundary."""

    return PlatformIntelligenceReviewAPI(source=source)


__all__ = [
    "PlatformIntelligenceReviewAPI",
    "PlatformIntelligenceReviewNotConfigured",
    "create_platform_intelligence_review_api",
]
