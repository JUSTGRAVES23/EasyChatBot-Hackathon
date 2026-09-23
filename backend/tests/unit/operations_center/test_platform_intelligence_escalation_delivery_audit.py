from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.application.operations_center.platform_intelligence_escalation_delivery_audit import (
    PlatformIntelligenceEscalationDeliveryAuditRecord,
    PlatformIntelligenceEscalationDeliveryAuditStatus,
)


def common(status):
    return PlatformIntelligenceEscalationDeliveryAuditRecord(
        audit_id=uuid4(),
        notification_key="platform_intelligence_escalation:REC-1",
        recommendation_id="REC-1",
        risk_decision_id="DEC-1",
        review_item_id="REV-1",
        correlation_id="CORR-1",
        attempt=1,
        status=status,
        occurred_at=datetime.now(timezone.utc),
        provider_message_id="provider-1"
        if status is PlatformIntelligenceEscalationDeliveryAuditStatus.SUCCEEDED
        else None,
        error_code="PROVIDER_ERROR"
        if status is PlatformIntelligenceEscalationDeliveryAuditStatus.FAILED
        else None,
    )


def test_audit_record_is_immutable():
    record = common(PlatformIntelligenceEscalationDeliveryAuditStatus.STARTED)
    with pytest.raises((AttributeError, TypeError)):
        record.attempt = 2


def test_success_requires_provider_message_id():
    with pytest.raises(ValueError, match="provider_message_id"):
        PlatformIntelligenceEscalationDeliveryAuditRecord(
            audit_id=uuid4(),
            notification_key="k",
            recommendation_id="r",
            risk_decision_id="d",
            review_item_id="v",
            correlation_id="c",
            attempt=1,
            status=PlatformIntelligenceEscalationDeliveryAuditStatus.SUCCEEDED,
            occurred_at=datetime.now(timezone.utc),
        )


def test_failure_requires_error_code():
    with pytest.raises(ValueError, match="error_code"):
        PlatformIntelligenceEscalationDeliveryAuditRecord(
            audit_id=uuid4(),
            notification_key="k",
            recommendation_id="r",
            risk_decision_id="d",
            review_item_id="v",
            correlation_id="c",
            attempt=1,
            status=PlatformIntelligenceEscalationDeliveryAuditStatus.FAILED,
            occurred_at=datetime.now(timezone.utc),
        )
