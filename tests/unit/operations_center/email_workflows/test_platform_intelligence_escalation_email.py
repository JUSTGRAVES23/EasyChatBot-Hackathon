from __future__ import annotations

import pytest

from app.application.operations_center.platform_intelligence_escalation_email import (
    PlatformIntelligenceEscalationEmailRequest,
    PlatformIntelligenceEscalationEmailService,
)


class Sender:
    def __init__(self) -> None:
        self.calls = []

    def send(
        self,
        request,
        *,
        subject,
        body,
        html_body,
    ):
        self.calls.append(
            (
                request,
                subject,
                body,
                html_body,
            )
        )
        return {
            "status": "accepted",
            "message_id": "msg-1",
        }


def request(**overrides):
    values = dict(
        recommendation_id="REC-1",
        risk_decision_id="DEC-1",
        review_item_id="REV-1",
        scope="operations-center",
        risk_level="HIGH",
        risk_score=0.82,
        quality_gate_status="PASSED",
        review_status="IN_REVIEW",
        decision_status="PENDING_HUMAN_REVIEW",
        route="RISK_OWNER",
        reasons=(
            "risk_level=HIGH",
            "historical_recurrence_threshold_reached",
        ),
        evidence_references=("EVID-1",),
        historical_references=("HIST-1",),
        policy_id="PI-ESCALATION",
        policy_version="1.0",
        rationale=(
            "Controlled escalation recommended from governed evidence."
        ),
        generated_at="2026-09-22T10:00:00+00:00",
        notification_key=(
            "platform_intelligence_escalation:REC-1"
        ),
    )

    values.update(overrides)

    return PlatformIntelligenceEscalationEmailRequest(
        **values
    )


def test_build_email_contains_governed_traceability_and_control_language():
    service = PlatformIntelligenceEscalationEmailService(
        sender=Sender(),
        frontend_base_url="http://localhost:5173",
    )

    req = request()

    body = service.build_body(req)
    html = service.build_html(req)

    for value in (
        "REC-1",
        "DEC-1",
        "REV-1",
        "EVID-1",
        "HIST-1",
        "PI-ESCALATION",
        "human review",
    ):
        assert value.lower() in (
            body + html
        ).lower()

    assert "does not constitute" in body
    assert "/operations-center/compliance/reviews" in html
    assert "Notification key" not in body
    assert "Notification key" not in html
    assert "action required" in body.lower()
    assert "sla or response target" in body.lower()


def test_send_delegates_to_injected_sender():
    sender = Sender()

    service = PlatformIntelligenceEscalationEmailService(
        sender=sender,
    )

    service.send(request())

    assert len(sender.calls) == 1
    assert sender.calls[0][0].recommendation_id == "REC-1"
    assert "HIGH" in sender.calls[0][1]


def test_non_review_state_is_rejected():
    with pytest.raises(
        ValueError,
        match="pending human decision",
    ):
        request(
            decision_status="ACCEPTED"
        )


def test_failed_quality_gate_is_rejected():
    with pytest.raises(
        ValueError,
        match="passed quality gate",
    ):
        request(
            quality_gate_status="FAILED"
        )