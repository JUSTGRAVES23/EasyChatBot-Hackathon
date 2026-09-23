from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceAuthoritativeState:
    """Canonical persisted PI review state consumed by Operations Center.

    This is deliberately one aggregate. It is not a replacement for the
    underlying risk engine or a generic approval framework.
    """

    review_item_id: str
    risk_decision_id: str
    risk_assessment_id: str
    scope: str
    risk_level: str
    risk_score: float
    priority: str

    review_status: str
    decision_status: str
    quality_gate_status: str

    evidence_references: tuple[str, ...]
    historical_references: tuple[str, ...]

    policy_id: str
    policy_version: str
    created_at: datetime

    assigned_reviewer: str | None = None
    assigned_at: datetime | None = None
    review_due_at: datetime | None = None
    rationale: str = ""

    recommendation_status: str | None = None
    recommendation_route: str | None = None
    recommendation_reasons: tuple[str, ...] = ()
    recommendation_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "review_item_id",
            "risk_decision_id",
            "risk_assessment_id",
            "scope",
            "risk_level",
            "priority",
            "review_status",
            "decision_status",
            "quality_gate_status",
            "policy_id",
            "policy_version",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be blank.")

        if not 0.0 <= self.risk_score <= 1.0:
            raise ValueError("risk_score must be between 0 and 1.")

        if self.recommendation_status is None:
            if self.recommendation_id is not None:
                raise ValueError(
                    "recommendation_id requires recommendation_status."
                )
        elif not self.recommendation_status.strip():
            raise ValueError("recommendation_status must not be blank.")

        if self.recommendation_id is not None and not self.recommendation_id.strip():
            raise ValueError("recommendation_id must not be blank.")


class PlatformIntelligenceAuthoritativeStateRepository(Protocol):
    async def list_all(
        self,
    ) -> tuple[PlatformIntelligenceAuthoritativeState, ...]:
        ...

    async def get(
        self,
        review_item_id: str,
    ) -> PlatformIntelligenceAuthoritativeState | None:
        ...

    async def save(
        self,
        state: PlatformIntelligenceAuthoritativeState,
    ) -> None:
        ...

    async def get_by_recommendation_id(
        self,
        recommendation_id: str,
    ) -> PlatformIntelligenceAuthoritativeState | None:
        ...
