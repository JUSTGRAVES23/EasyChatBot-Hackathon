from __future__ import annotations

import asyncio

from app.application.operations_center.platform_intelligence_escalation_email import (
    PlatformIntelligenceEscalationEmailRequest,
)
from app.infrastructure.email.platform_intelligence_escalation_email_sender import (
    ResendPlatformIntelligenceEscalationEmailSender,
)


class Provider:
    def __init__(self) -> None:
        self.calls = []

    async def send(
        self,
        subject,
        content,
    ):
        self.calls.append(
            (
                subject,
                content,
            )
        )

        return {
            "status": "accepted",
            "message_id": "msg-1",
        }


class Manager:
    def __init__(self, provider):
        self.provider = provider

    def send(
        self,
        subject,
        content,
    ):
        return self.provider.send(
            subject,
            content,
        )


def make_request():
    return PlatformIntelligenceEscalationEmailRequest(
        recommendation_id="REC-1",
        risk_decision_id="DEC-1",
        review_item_id="REV-1",
        scope="operations-center",
        risk_level="HIGH",
        risk_score=0.8,
        quality_gate_status="PASSED",
        review_status="IN_REVIEW",
        decision_status="PENDING_HUMAN_REVIEW",
        route="RISK_OWNER",
        reasons=("risk_level=HIGH",),
        evidence_references=("E1",),
        historical_references=("H1",),
        policy_id="P",
        policy_version="1",
        rationale="rationale",
        generated_at="2026-09-22T10:00:00+00:00",
        notification_key=(
            "platform_intelligence_escalation:REC-1"
        ),
    )


def test_sender_uses_route_recipient_and_shared_provider():
    provider = Provider()

    sender = ResendPlatformIntelligenceEscalationEmailSender(
        provider_manager=Manager(provider),
        recipients={
            "RISK_OWNER": "risk-owner@example.test",
        },
    )

    result = sender.send(
        make_request(),
        subject="subject",
        body="body",
        html_body="<p>body</p>",
    )

    asyncio.run(result)

    subject, content = provider.calls[0]

    assert subject == "subject"
    assert (
        content["recipient"]
        == "risk-owner@example.test"
    )
    assert (
        content["email_type"]
        == "platform_intelligence_escalation"
    )
    assert (
        content["recommendation_id"]
        == "REC-1"
    )