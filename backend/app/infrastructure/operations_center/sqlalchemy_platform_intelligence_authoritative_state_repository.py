from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.operations_center.platform_intelligence_authoritative_state import (
    PlatformIntelligenceAuthoritativeState,
)


class SqlAlchemyPlatformIntelligenceAuthoritativeStateRepository:
    """PostgreSQL repository for the authoritative PI review aggregate."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def list_all(
        self,
    ) -> tuple[PlatformIntelligenceAuthoritativeState, ...]:
        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT *
                    FROM platform_intelligence_review_states
                    ORDER BY created_at ASC, review_item_id ASC
                    """
                )
            )
            return tuple(
                self._to_state(row)
                for row in result.mappings().all()
            )

    async def get(
        self,
        review_item_id: str,
    ) -> PlatformIntelligenceAuthoritativeState | None:
        if not review_item_id.strip():
            raise ValueError("review_item_id must not be blank.")

        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT *
                    FROM platform_intelligence_review_states
                    WHERE review_item_id = :review_item_id
                    """
                ),
                {"review_item_id": review_item_id},
            )
            row = result.mappings().first()
            return self._to_state(row) if row is not None else None

    async def get_by_recommendation_id(
        self,
        recommendation_id: str,
    ) -> PlatformIntelligenceAuthoritativeState | None:
        if not recommendation_id.strip():
            raise ValueError("recommendation_id must not be blank.")

        async with self._session_factory() as session:
            result = await session.execute(
                text(
                    """
                    SELECT *
                    FROM platform_intelligence_review_states
                    WHERE recommendation_id = :recommendation_id
                    """
                ),
                {"recommendation_id": recommendation_id},
            )
            row = result.mappings().first()
            return self._to_state(row) if row is not None else None

    async def save(
        self,
        state: PlatformIntelligenceAuthoritativeState,
    ) -> None:
        async with self._session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO platform_intelligence_review_states (
                        review_item_id,
                        risk_decision_id,
                        risk_assessment_id,
                        scope,
                        risk_level,
                        risk_score,
                        priority,
                        review_status,
                        decision_status,
                        quality_gate_status,
                        evidence_references,
                        historical_references,
                        policy_id,
                        policy_version,
                        created_at,
                        assigned_reviewer,
                        assigned_at,
                        review_due_at,
                        rationale,
                        recommendation_status,
                        recommendation_route,
                        recommendation_reasons,
                        recommendation_id,
                        updated_at
                    )
                    VALUES (
                        :review_item_id,
                        :risk_decision_id,
                        :risk_assessment_id,
                        :scope,
                        :risk_level,
                        :risk_score,
                        :priority,
                        :review_status,
                        :decision_status,
                        :quality_gate_status,
                        CAST(:evidence_references AS JSONB),
                        CAST(:historical_references AS JSONB),
                        :policy_id,
                        :policy_version,
                        :created_at,
                        :assigned_reviewer,
                        :assigned_at,
                        :review_due_at,
                        :rationale,
                        :recommendation_status,
                        :recommendation_route,
                        CAST(:recommendation_reasons AS JSONB),
                        :recommendation_id,
                        CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (review_item_id)
                    DO UPDATE SET
                        risk_decision_id = EXCLUDED.risk_decision_id,
                        risk_assessment_id = EXCLUDED.risk_assessment_id,
                        scope = EXCLUDED.scope,
                        risk_level = EXCLUDED.risk_level,
                        risk_score = EXCLUDED.risk_score,
                        priority = EXCLUDED.priority,
                        review_status = EXCLUDED.review_status,
                        decision_status = EXCLUDED.decision_status,
                        quality_gate_status = EXCLUDED.quality_gate_status,
                        evidence_references = EXCLUDED.evidence_references,
                        historical_references = EXCLUDED.historical_references,
                        policy_id = EXCLUDED.policy_id,
                        policy_version = EXCLUDED.policy_version,
                        assigned_reviewer = EXCLUDED.assigned_reviewer,
                        assigned_at = EXCLUDED.assigned_at,
                        review_due_at = EXCLUDED.review_due_at,
                        rationale = EXCLUDED.rationale,
                        recommendation_status = EXCLUDED.recommendation_status,
                        recommendation_route = EXCLUDED.recommendation_route,
                        recommendation_reasons = EXCLUDED.recommendation_reasons,
                        recommendation_id = EXCLUDED.recommendation_id,
                        updated_at = CURRENT_TIMESTAMP
                    """
                ),
                self._params(state),
            )
            await session.commit()

    @staticmethod
    def _params(
        state: PlatformIntelligenceAuthoritativeState,
    ) -> dict[str, Any]:
        return {
            "review_item_id": state.review_item_id,
            "risk_decision_id": state.risk_decision_id,
            "risk_assessment_id": state.risk_assessment_id,
            "scope": state.scope,
            "risk_level": state.risk_level,
            "risk_score": state.risk_score,
            "priority": state.priority,
            "review_status": state.review_status,
            "decision_status": state.decision_status,
            "quality_gate_status": state.quality_gate_status,
            "evidence_references": json.dumps(state.evidence_references),
            "historical_references": json.dumps(state.historical_references),
            "policy_id": state.policy_id,
            "policy_version": state.policy_version,
            "created_at": state.created_at,
            "assigned_reviewer": state.assigned_reviewer,
            "assigned_at": state.assigned_at,
            "review_due_at": state.review_due_at,
            "rationale": state.rationale,
            "recommendation_status": state.recommendation_status,
            "recommendation_route": state.recommendation_route,
            "recommendation_reasons": json.dumps(state.recommendation_reasons),
            "recommendation_id": state.recommendation_id,
        }

    @staticmethod
    def _to_state(
        row: Mapping[str, Any],
    ) -> PlatformIntelligenceAuthoritativeState:
        return PlatformIntelligenceAuthoritativeState(
            review_item_id=str(row["review_item_id"]),
            risk_decision_id=str(row["risk_decision_id"]),
            risk_assessment_id=str(row["risk_assessment_id"]),
            scope=str(row["scope"]),
            risk_level=str(row["risk_level"]),
            risk_score=float(row["risk_score"]),
            priority=str(row["priority"]),
            review_status=str(row["review_status"]),
            decision_status=str(row["decision_status"]),
            quality_gate_status=str(row["quality_gate_status"]),
            evidence_references=tuple(row["evidence_references"] or ()),
            historical_references=tuple(row["historical_references"] or ()),
            policy_id=str(row["policy_id"]),
            policy_version=str(row["policy_version"]),
            created_at=row["created_at"],
            assigned_reviewer=row["assigned_reviewer"],
            assigned_at=row["assigned_at"],
            review_due_at=row["review_due_at"],
            rationale=str(row["rationale"] or ""),
            recommendation_status=row["recommendation_status"],
            recommendation_route=row["recommendation_route"],
            recommendation_reasons=tuple(row["recommendation_reasons"] or ()),
            recommendation_id=row["recommendation_id"],
        )
