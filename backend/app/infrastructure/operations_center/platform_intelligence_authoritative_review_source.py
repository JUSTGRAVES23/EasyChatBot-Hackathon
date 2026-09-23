from __future__ import annotations

from dataclasses import asdict
from typing import Any

from app.application.operations_center.platform_intelligence_authoritative_state import (
    PlatformIntelligenceAuthoritativeStateRepository,
)
from app.application.operations_center.platform_intelligence_escalation_retry_orchestrator import (
    PlatformIntelligenceRetryStateReader,
)
from app.application.operations_center.platform_intelligence_escalation_retry_orchestration import (
    PlatformIntelligenceRetryState,
)
from app.application.operations_center.platform_intelligence_review_source import (
    PlatformIntelligenceReviewSource,
)


class PostgreSQLPlatformIntelligenceReviewSource(
    PlatformIntelligenceReviewSource,
    PlatformIntelligenceRetryStateReader,
):
    """
    Production read adapter over authoritative Platform Intelligence state.

    Architecture boundary:

        PostgreSQL authoritative PI state
                    |
                    v
        PostgreSQLPlatformIntelligenceReviewSource
                    |
              +-----+------+
              |            |
              v            v
        Review projection  Retry state
              |            |
              v            v
        Review API     Retry Orchestrator

    Responsibilities:
    - read authoritative PI state;
    - expose the governed review projection;
    - expose recommended escalations;
    - rehydrate the existing retry-state contract.

    Non-responsibilities:
    - no retry policy;
    - no dispatch;
    - no email sending;
    - no delivery persistence;
    - no scheduler;
    - no mutation of risk/review state.
    """

    def __init__(
        self,
        repository: PlatformIntelligenceAuthoritativeStateRepository,
    ) -> None:
        if repository is None:
            raise ValueError("repository must not be None.")

        self._repository = repository

    # ------------------------------------------------------------------
    # Existing ReviewSource synchronous contract
    # ------------------------------------------------------------------
    #
    # The current ReviewSource application boundary is synchronous,
    # while authoritative persistence is asynchronous.
    #
    # The async methods below are therefore the production persistence
    # adapter entry points. These synchronous methods intentionally fail
    # closed rather than performing unsafe event-loop manipulation.
    #
    # Composition must use the async methods when binding this adapter
    # to the async PostgreSQL repository.

    def list_reviews(self) -> tuple[Any, ...]:
        raise RuntimeError(
            "Use list_reviews_async() from the async application composition."
        )

    def get_review(
        self,
        review_item_id: str,
    ) -> Any | None:
        raise RuntimeError(
            "Use get_review_async() from the async application composition."
        )

    def list_escalations(self) -> tuple[Any, ...]:
        raise RuntimeError(
            "Use list_escalations_async() from the async application composition."
        )

    # ------------------------------------------------------------------
    # Async authoritative-state API
    # ------------------------------------------------------------------

    async def list_reviews_async(
        self,
    ) -> tuple[dict[str, Any], ...]:
        states = await self._repository.list_all()

        return tuple(
            self._projection(state)
            for state in states
        )

    async def get_review_async(
        self,
        review_item_id: str,
    ) -> dict[str, Any] | None:
        if not review_item_id or not review_item_id.strip():
            raise ValueError("review_item_id must not be blank.")

        state = await self._repository.get(review_item_id)

        if state is None:
            return None

        return self._projection(state)

    async def list_escalations_async(
        self,
    ) -> tuple[dict[str, Any], ...]:
        states = await self._repository.list_all()

        return tuple(
            self._projection(state)
            for state in states
            if state.recommendation_status == "RECOMMENDED"
        )

    # ------------------------------------------------------------------
    # Retry State Reader
    # ------------------------------------------------------------------

    async def get_retry_state(
        self,
        notification_key: str,
        recommendation_id: str,
    ) -> PlatformIntelligenceRetryState | None:
        if not notification_key or not notification_key.strip():
            raise ValueError("notification_key must not be blank.")

        if not recommendation_id or not recommendation_id.strip():
            raise ValueError("recommendation_id must not be blank.")

        state = await self._repository.get_by_recommendation_id(
            recommendation_id
        )

        if state is None:
            return None

        if state.recommendation_id != recommendation_id:
            return None

        return PlatformIntelligenceRetryState(
            notification_key=notification_key,
            recommendation_id=recommendation_id,
            recommendation_status=state.recommendation_status or "",
            review_status=state.review_status,
            decision_status=state.decision_status,
            quality_gate_status=state.quality_gate_status,
            dispatch_request=self._dispatch_request(
                state,
                notification_key,
            ),
            email_request=self._email_request(
                state,
                notification_key,
            ),
        )

    # ------------------------------------------------------------------
    # Projection
    # ------------------------------------------------------------------

    @staticmethod
    def _projection(
        state: Any,
    ) -> dict[str, Any]:
        """
        Return the persisted authoritative state as the governed
        Operations Center projection.

        The aggregate is immutable, so asdict() is safe here and keeps
        this adapter free from a second projection model.
        """
        return asdict(state)

    # ------------------------------------------------------------------
    # Existing canonical dispatch contract
    # ------------------------------------------------------------------

    @staticmethod
    def _dispatch_request(
        state: Any,
        notification_key: str,
    ) -> Any:
        """
        Rehydrate the existing canonical PI escalation dispatch request.

        This adapter does not implement dispatch behaviour. It only
        reconstructs the immutable request consumed by the existing
        dispatch service.
        """
        from app.application.operations_center.platform_intelligence_escalation_dispatch import (
            PlatformIntelligenceEscalationDispatchRequest,
        )

        return PlatformIntelligenceEscalationDispatchRequest(
            notification_key=notification_key,
            recommendation_id=state.recommendation_id or "",
            risk_decision_id=state.risk_decision_id,
            review_item_id=state.review_item_id,
            risk_level=state.risk_level,
            risk_score=state.risk_score,
            quality_gate_status=state.quality_gate_status,
            review_status=state.review_status,
            decision_status=state.decision_status,
            correlation_id=notification_key,
            route=state.recommendation_route or "",
            reasons=state.recommendation_reasons,
        )

    # ------------------------------------------------------------------
    # Existing canonical email contract
    # ------------------------------------------------------------------

    @staticmethod
    def _email_request(
        state: Any,
        notification_key: str,
    ) -> Any:
        """
        Rehydrate the existing canonical PI escalation email request.

        The authoritative state contains created_at, not updated_at.
        created_at is therefore the authoritative timestamp used for
        generated_at during retry-state reconstruction.
        """
        from app.application.operations_center.platform_intelligence_escalation_email import (
            PlatformIntelligenceEscalationEmailRequest,
        )

        return PlatformIntelligenceEscalationEmailRequest(
            recommendation_id=state.recommendation_id or "",
            risk_decision_id=state.risk_decision_id,
            review_item_id=state.review_item_id,
            scope=state.scope,
            risk_level=state.risk_level,
            risk_score=state.risk_score,
            quality_gate_status=state.quality_gate_status,
            review_status=state.review_status,
            decision_status=state.decision_status,
            route=state.recommendation_route or "",
            reasons=state.recommendation_reasons,
            evidence_references=state.evidence_references,
            historical_references=state.historical_references,
            policy_id=state.policy_id,
            policy_version=state.policy_version,
            rationale=state.rationale,
            generated_at=state.created_at.isoformat(),
            notification_key=notification_key,
        )


__all__ = [
    "PostgreSQLPlatformIntelligenceReviewSource",
]