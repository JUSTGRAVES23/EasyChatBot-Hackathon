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


async def test_get_missing_notification_returns_none() -> None:
    _database_required()

    engine = create_async_database_engine()
    try:
        repository = SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
            create_async_session_factory(engine)
        )

        assert await repository.get_by_notification_key(
            f"pi-test-missing-{uuid4()}"
        ) is None
    finally:
        await engine.dispose()


async def test_started_success_and_idempotent_record_round_trip() -> None:
    _database_required()

    engine = create_async_database_engine()
    key = f"pi-test-{uuid4()}"

    try:
        repository = SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
            create_async_session_factory(engine)
        )

        started = await repository.create_started(
            notification_key=key,
            recommendation_id="recommendation-test",
            risk_decision_id="decision-test",
            review_item_id="review-test",
            correlation_id="correlation-test",
        )

        assert started.status is PlatformIntelligenceEscalationDeliveryStatus.STARTED
        assert started.attempt == 1

        succeeded = await repository.mark_succeeded(
            notification_key=key,
            provider_message_id="provider-message-1",
        )

        assert (
            succeeded.status
            is PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED
        )
        assert succeeded.provider_message_id == "provider-message-1"
        assert succeeded.attempt == 1

        loaded = await repository.get_by_notification_key(key)

        assert loaded is not None
        assert (
            loaded.status
            is PlatformIntelligenceEscalationDeliveryStatus.SUCCEEDED
        )
        assert loaded.provider_message_id == "provider-message-1"
    finally:
        await engine.dispose()


async def test_failed_delivery_can_retry_with_incremented_attempt() -> None:
    _database_required()

    engine = create_async_database_engine()
    key = f"pi-test-retry-{uuid4()}"

    try:
        repository = SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
            create_async_session_factory(engine)
        )

        await repository.create_started(
            notification_key=key,
            recommendation_id="recommendation-retry",
            risk_decision_id="decision-retry",
            review_item_id="review-retry",
            correlation_id="correlation-retry",
        )

        failed = await repository.mark_failed(
            notification_key=key,
            error_code="PROVIDER_ERROR",
        )

        assert failed.status is PlatformIntelligenceEscalationDeliveryStatus.FAILED
        assert failed.attempt == 1
        assert failed.error_code == "PROVIDER_ERROR"

        retried = await repository.start_retry(
            notification_key=key,
        )

        assert retried.status is PlatformIntelligenceEscalationDeliveryStatus.STARTED
        assert retried.attempt == 2
        assert retried.provider_message_id is None
        assert retried.error_code is None
    finally:
        await engine.dispose()


async def test_list_retry_candidates_returns_only_failed_and_started_in_deterministic_order() -> None:
    _database_required()

    engine = create_async_database_engine()
    suffix = uuid4()

    started_key = f"pi-test-candidate-started-{suffix}"
    failed_key = f"pi-test-candidate-failed-{suffix}"
    succeeded_key = f"pi-test-candidate-succeeded-{suffix}"

    test_keys = (
        started_key,
        failed_key,
        succeeded_key,
    )

    try:
        repository = SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
            create_async_session_factory(engine)
        )

        await repository.create_started(
            notification_key=started_key,
            recommendation_id=f"recommendation-started-{suffix}",
            risk_decision_id=f"decision-started-{suffix}",
            review_item_id=f"review-started-{suffix}",
            correlation_id=f"correlation-started-{suffix}",
        )

        await repository.create_started(
            notification_key=failed_key,
            recommendation_id=f"recommendation-failed-{suffix}",
            risk_decision_id=f"decision-failed-{suffix}",
            review_item_id=f"review-failed-{suffix}",
            correlation_id=f"correlation-failed-{suffix}",
        )

        await repository.mark_failed(
            notification_key=failed_key,
            error_code="PROVIDER_ERROR",
        )

        await repository.create_started(
            notification_key=succeeded_key,
            recommendation_id=f"recommendation-succeeded-{suffix}",
            risk_decision_id=f"decision-succeeded-{suffix}",
            review_item_id=f"review-succeeded-{suffix}",
            correlation_id=f"correlation-succeeded-{suffix}",
        )

        await repository.mark_succeeded(
            notification_key=succeeded_key,
            provider_message_id="provider-message-succeeded",
        )

        # Establish a deterministic ordering for this test's records.
        #
        # The production repository deliberately returns the global retry
        # candidate set. This test therefore retrieves a sufficiently large
        # bounded batch and then isolates its own records for assertions.
        older = datetime.now(timezone.utc) - timedelta(minutes=5)
        newer = datetime.now(timezone.utc) - timedelta(minutes=1)

        async with repository._session_factory() as session:  # noqa: SLF001
            await session.execute(
                text(
                    """
                    UPDATE platform_intelligence_escalation_deliveries
                    SET updated_at = :updated_at
                    WHERE notification_key = :notification_key
                    """
                ),
                {
                    "updated_at": older,
                    "notification_key": failed_key,
                },
            )

            await session.execute(
                text(
                    """
                    UPDATE platform_intelligence_escalation_deliveries
                    SET updated_at = :updated_at
                    WHERE notification_key = :notification_key
                    """
                ),
                {
                    "updated_at": newer,
                    "notification_key": started_key,
                },
            )

            await session.commit()

        # The table is shared across integration-test runs, so previous
        # FAILED/STARTED records may legitimately exist. Do not let those
        # unrelated records consume the small production-style limit used
        # by the test.
        candidates = await repository.list_retry_candidates(
            limit=1000,
        )

        candidate_by_key = {
            record.notification_key: record
            for record in candidates
            if record.notification_key in test_keys
        }

        assert failed_key in candidate_by_key
        assert started_key in candidate_by_key
        assert succeeded_key not in candidate_by_key

        own_candidate_keys = [
            record.notification_key
            for record in candidates
            if record.notification_key in test_keys
        ]

        assert own_candidate_keys == [
            failed_key,
            started_key,
        ]

        assert all(
            record.status
            in (
                PlatformIntelligenceEscalationDeliveryStatus.FAILED,
                PlatformIntelligenceEscalationDeliveryStatus.STARTED,
            )
            for record in (
                candidate_by_key[failed_key],
                candidate_by_key[started_key],
            )
        )
    finally:
        # Clean up only this test's own records.
        async with repository._session_factory() as session:  # noqa: SLF001
            await session.execute(
                text(
                    """
                    DELETE FROM platform_intelligence_escalation_deliveries
                    WHERE notification_key IN (
                        :started_key,
                        :failed_key,
                        :succeeded_key
                    )
                    """
                ),
                {
                    "started_key": started_key,
                    "failed_key": failed_key,
                    "succeeded_key": succeeded_key,
                },
            )
            await session.commit()

        await engine.dispose()


async def test_list_retry_candidates_respects_limit() -> None:
    _database_required()

    engine = create_async_database_engine()
    suffix = uuid4()

    keys = [
        f"pi-test-candidate-limit-{suffix}-{index}"
        for index in range(3)
    ]

    try:
        repository = SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(
            create_async_session_factory(engine)
        )

        for index, key in enumerate(keys):
            await repository.create_started(
                notification_key=key,
                recommendation_id=f"recommendation-limit-{suffix}-{index}",
                risk_decision_id=f"decision-limit-{suffix}-{index}",
                review_item_id=f"review-limit-{suffix}-{index}",
                correlation_id=f"correlation-limit-{suffix}-{index}",
            )

            await repository.mark_failed(
                notification_key=key,
                error_code="PROVIDER_ERROR",
            )

        # Use a sufficiently large query window so unrelated historical
        # integration-test rows cannot prevent this test's own records from
        # being discovered.
        candidates = await repository.list_retry_candidates(
            limit=1000,
        )

        own_candidates = [
            record
            for record in candidates
            if record.notification_key in keys
        ]

        assert len(own_candidates) == 3

        # Validate the actual repository limit independently.
        limited_candidates = await repository.list_retry_candidates(
            limit=2,
        )

        assert len(limited_candidates) <= 2
    finally:
        async with repository._session_factory() as session:  # noqa: SLF001
            await session.execute(
                text(
                    """
                    DELETE FROM platform_intelligence_escalation_deliveries
                    WHERE notification_key IN (
                        :key_0,
                        :key_1,
                        :key_2
                    )
                    """
                ),
                {
                    "key_0": keys[0],
                    "key_1": keys[1],
                    "key_2": keys[2],
                },
            )
            await session.commit()

        await engine.dispose()