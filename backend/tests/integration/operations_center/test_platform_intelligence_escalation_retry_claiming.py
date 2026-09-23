from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.infrastructure.operations_center.sqlalchemy_platform_intelligence_escalation_delivery_repository import (
    SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository,
)
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
)


pytestmark = pytest.mark.asyncio


def _database_required() -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests.")


async def test_claim_retry_candidate_is_atomic_and_reclaimable_after_lease_expiry() -> None:
    _database_required()

    engine = create_async_database_engine()
    key = f"pi-claim-{uuid4()}"

    try:
        repository = SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
            create_async_session_factory(engine)
        )

        await repository.create_started(
            notification_key=key,
            recommendation_id=f"recommendation-{uuid4()}",
            risk_decision_id=f"decision-{uuid4()}",
            review_item_id=f"review-{uuid4()}",
            correlation_id=f"correlation-{uuid4()}",
        )
        await repository.mark_failed(
            notification_key=key,
            error_code="PROVIDER_ERROR",
        )

        first_token = str(uuid4())
        first_claimed_at = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
        first_expiry = first_claimed_at + timedelta(minutes=5)

        first = await repository.claim_retry_candidate(
            notification_key=key,
            claim_token=first_token,
            claimed_at=first_claimed_at,
            lease_expires_at=first_expiry,
        )
        assert first is True

        second = await repository.claim_retry_candidate(
            notification_key=key,
            claim_token=str(uuid4()),
            claimed_at=first_claimed_at + timedelta(seconds=1),
            lease_expires_at=first_expiry + timedelta(seconds=1),
        )
        assert second is False

        third_token = str(uuid4())
        third_claimed_at = first_expiry + timedelta(seconds=1)
        third = await repository.claim_retry_candidate(
            notification_key=key,
            claim_token=third_token,
            claimed_at=third_claimed_at,
            lease_expires_at=third_claimed_at + timedelta(minutes=5),
        )
        assert third is True

        async with repository._session_factory() as session:  # noqa: SLF001
            row = (
                await session.execute(
                    text(
                        """
                        SELECT claim_token, claimed_at, lease_expires_at
                        FROM platform_intelligence_escalation_deliveries
                        WHERE notification_key = :notification_key
                        """
                    ),
                    {"notification_key": key},
                )
            ).mappings().one()

        assert row["claim_token"] == third_token
        assert row["claimed_at"] == third_claimed_at
    finally:
        async with repository._session_factory() as session:  # noqa: SLF001
            await session.execute(
                text(
                    """
                    DELETE FROM platform_intelligence_escalation_deliveries
                    WHERE notification_key = :notification_key
                    """
                ),
                {"notification_key": key},
            )
            await session.commit()
        await engine.dispose()


async def test_claim_does_not_claim_succeeded_delivery() -> None:
    _database_required()

    engine = create_async_database_engine()
    key = f"pi-claim-success-{uuid4()}"

    try:
        repository = SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
            create_async_session_factory(engine)
        )

        await repository.create_started(
            notification_key=key,
            recommendation_id=f"recommendation-{uuid4()}",
            risk_decision_id=f"decision-{uuid4()}",
            review_item_id=f"review-{uuid4()}",
            correlation_id=f"correlation-{uuid4()}",
        )
        await repository.mark_succeeded(
            notification_key=key,
            provider_message_id="provider-message",
        )

        claimed = await repository.claim_retry_candidate(
            notification_key=key,
            claim_token=str(uuid4()),
            claimed_at=datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc),
            lease_expires_at=datetime(
                2026, 9, 22, 12, 5, tzinfo=timezone.utc
            ),
        )

        assert claimed is False
    finally:
        async with repository._session_factory() as session:  # noqa: SLF001
            await session.execute(
                text(
                    """
                    DELETE FROM platform_intelligence_escalation_deliveries
                    WHERE notification_key = :notification_key
                    """
                ),
                {"notification_key": key},
            )
            await session.commit()
        await engine.dispose()
