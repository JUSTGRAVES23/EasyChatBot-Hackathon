from __future__ import annotations

import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application.operations_center.platform_intelligence_escalation_delivery import (
    PlatformIntelligenceEscalationDeliveryStatus,
)
from app.application.operations_center.platform_intelligence_escalation_delivery_audit import (
    PlatformIntelligenceEscalationDeliveryAuditStatus,
)
from app.infrastructure.operations_center.sqlalchemy_platform_intelligence_escalation_delivery_repository import (
    SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository,
)
from app.infrastructure.operations_center.sqlalchemy_platform_intelligence_escalation_delivery_audit_repository import (
    SqlAlchemyPlatformIntelligenceEscalationDeliveryAuditRepository,
)
from app.infrastructure.persistence.database import (
    create_async_database_engine,
    create_async_session_factory,
)

pytestmark = pytest.mark.asyncio


def required():
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for PostgreSQL integration tests.")


async def test_delivery_lifecycle_is_durably_audited():
    required()
    engine = create_async_database_engine()
    key = f"pi-audit-lifecycle-{uuid4()}"

    try:
        factory = create_async_session_factory(engine)
        delivery = SqlAlchemyPlatformIntelligenceEscalationDeliveryRepository(factory)
        audit = SqlAlchemyPlatformIntelligenceEscalationDeliveryAuditRepository(factory)

        await delivery.create_started(
            notification_key=key,
            recommendation_id="REC-AUDIT",
            risk_decision_id="DEC-AUDIT",
            review_item_id="REV-AUDIT",
            correlation_id="CORR-AUDIT",
        )
        await delivery.mark_failed(
            notification_key=key,
            error_code="PROVIDER_ERROR",
        )
        await delivery.start_retry(notification_key=key)
        await delivery.mark_succeeded(
            notification_key=key,
            provider_message_id="provider-audit-2",
        )

        events = await audit.list_by_notification_key(key)

        assert [event.status for event in events] == [
            PlatformIntelligenceEscalationDeliveryAuditStatus.STARTED,
            PlatformIntelligenceEscalationDeliveryAuditStatus.FAILED,
            PlatformIntelligenceEscalationDeliveryAuditStatus.STARTED,
            PlatformIntelligenceEscalationDeliveryAuditStatus.SUCCEEDED,
        ]
        assert [event.attempt for event in events] == [1, 1, 2, 2]
        assert events[1].error_code == "PROVIDER_ERROR"
        assert events[-1].provider_message_id == "provider-audit-2"
    finally:
        async with create_async_session_factory(engine)() as session:
            await session.execute(
                text(
                    """
                    DELETE FROM platform_intelligence_escalation_delivery_audit
                    WHERE notification_key = :key
                    """
                ),
                {"key": key},
            )
            await session.execute(
                text(
                    """
                    DELETE FROM platform_intelligence_escalation_deliveries
                    WHERE notification_key = :key
                    """
                ),
                {"key": key},
            )
            await session.commit()
        await engine.dispose()
