"""Governed Platform Intelligence escalation email workflow.

This application service prepares and dispatches an escalation notification only
when a governed PI escalation recommendation is present.

It does not create, accept, reject, or otherwise change the underlying
risk decision.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, replace
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class PlatformIntelligenceEscalationEmailRequest:
    """Immutable, traceable email request for a PI escalation recommendation."""

    recommendation_id: str
    risk_decision_id: str
    review_item_id: str
    scope: str
    risk_level: str
    risk_score: float
    quality_gate_status: str
    review_status: str
    decision_status: str
    route: str
    reasons: tuple[str, ...]
    evidence_references: tuple[str, ...]
    historical_references: tuple[str, ...]
    policy_id: str
    policy_version: str
    rationale: str
    generated_at: str
    review_url: str | None = None
    notification_key: str = ""
    delivery: Any | None = None

    def __post_init__(self) -> None:
        required = {
            "recommendation_id": self.recommendation_id,
            "risk_decision_id": self.risk_decision_id,
            "review_item_id": self.review_item_id,
            "scope": self.scope,
            "risk_level": self.risk_level,
            "quality_gate_status": self.quality_gate_status,
            "review_status": self.review_status,
            "decision_status": self.decision_status,
            "route": self.route,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "rationale": self.rationale,
            "generated_at": self.generated_at,
        }

        for name, value in required.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required.")

        if not 0.0 <= self.risk_score <= 1.0:
            raise ValueError("risk_score must be between 0 and 1.")

        if self.quality_gate_status != "PASSED":
            raise ValueError(
                "Escalation email requires a passed quality gate."
            )

        if not self.notification_key.strip():
            raise ValueError("notification_key is required.")

        if self.decision_status != "PENDING_HUMAN_REVIEW":
            raise ValueError(
                "Escalation email requires a pending human decision."
            )

        if self.review_status != "IN_REVIEW":
            raise ValueError(
                "Escalation email requires an IN_REVIEW item."
            )

        if any(not value.strip() for value in self.reasons):
            raise ValueError("reasons cannot contain blanks.")

        if any(
            not value.strip()
            for value in self.evidence_references
        ):
            raise ValueError(
                "evidence_references cannot contain blanks."
            )

        if any(
            not value.strip()
            for value in self.historical_references
        ):
            raise ValueError(
                "historical_references cannot contain blanks."
            )


class PlatformIntelligenceEscalationEmailSender(Protocol):
    """Provider-independent delivery boundary."""

    def send(
        self,
        request: PlatformIntelligenceEscalationEmailRequest,
        *,
        subject: str,
        body: str,
        html_body: str,
    ) -> object:
        ...


class PlatformIntelligenceEscalationEmailService:
    """Prepare and dispatch governed PI escalation notifications.

    The service requires the caller to supply the authoritative PI review
    projection. It does not query the runtime, risk engine, or repositories.
    """

    workflow_id = "platform_intelligence_escalation"
    template_id = "platform_intelligence_escalation"

    def __init__(
        self,
        *,
        sender: PlatformIntelligenceEscalationEmailSender,
        workflow_active: bool = True,
        frontend_base_url: str | None = None,
    ) -> None:
        if sender is None:
            raise ValueError("sender is required.")

        self._sender = sender
        self._workflow_active = workflow_active
        self._frontend_base_url = (
            (frontend_base_url or "").strip().rstrip("/")
        )

    def prepare(
        self,
        request: PlatformIntelligenceEscalationEmailRequest,
    ) -> PlatformIntelligenceEscalationEmailRequest:
        if request is None:
            raise ValueError("request is required.")

        if not self._workflow_active:
            raise ValueError(
                "Platform Intelligence escalation email workflow "
                "is not active."
            )

        if not request.route.strip():
            raise ValueError("Escalation route is required.")

        return request

    def build_subject(
        self,
        request: PlatformIntelligenceEscalationEmailRequest,
    ) -> str:
        self.prepare(request)

        return (
            "[EasyWorld Platform Intelligence] "
            f"{request.risk_level} escalation review required "
            f"— {request.scope}"
        )

    def build_body(
        self,
        request: PlatformIntelligenceEscalationEmailRequest,
    ) -> str:
        self.prepare(request)

        lines = [
            "EASYWORLD · PLATFORM INTELLIGENCE",
            "",
            "HUMAN ESCALATION REVIEW REQUIRED",
            "",
            (
                "A governed Platform Intelligence escalation "
                "recommendation has been generated."
            ),
            (
                "This notification is a recommendation for human "
                "review only. It does not"
            ),
            (
                "constitute approval, rejection, remediation "
                "authorization, or production action."
            ),
            "",
            "RISK",
            f"Scope: {request.scope}",
            f"Risk level: {request.risk_level}",
            f"Risk score: {request.risk_score:.4f}",
            f"Escalation route: {request.route}",
            "",
            "TRACEABILITY",
            f"Recommendation ID: {request.recommendation_id}",
            f"Risk decision ID: {request.risk_decision_id}",
            f"Review item ID: {request.review_item_id}",
            f"Generated at: {request.generated_at}",
            "",
            "GOVERNANCE",
            f"Quality gate: {request.quality_gate_status}",
            f"Review status: {request.review_status}",
            f"Decision status: {request.decision_status}",
            f"Policy: {request.policy_id} / {request.policy_version}",
            "",
            "ESCALATION REASONS",
            *[
                f"- {reason}"
                for reason in request.reasons
            ],
            "",
            "EVIDENCE REFERENCES",
            *[
                f"- {reference}"
                for reference in request.evidence_references
            ],
            "",
            "HISTORICAL REFERENCES",
            *[
                f"- {reference}"
                for reference in request.historical_references
            ],
            "",
            "ASSESSMENT RATIONALE",
            request.rationale,
            "",
            "ACTION REQUIRED",
            (
                "Open the authoritative Platform Intelligence review "
                "record and complete the human review in the controlled "
                "system. Do not approve, reject, or authorize remediation "
                "from the email itself. Any SLA or response target is "
                "governed by the authoritative review record and "
                "escalation policy."
            ),
            "",
            "DECISION CONTROL",
            (
                "Email reply does not constitute acceptance, rejection, "
                "or authorization."
            ),
        ]

        if request.review_url:
            lines.extend(
                [
                    "",
                    "REVIEW",
                    request.review_url,
                ]
            )

        return "\n".join(lines)

    def build_html(
        self,
        request: PlatformIntelligenceEscalationEmailRequest,
    ) -> str:
        self.prepare(request)
        return _build_html(
            request,
            self._frontend_base_url,
        )

    def send(
        self,
        request: PlatformIntelligenceEscalationEmailRequest,
    ) -> PlatformIntelligenceEscalationEmailRequest:
        self.prepare(request)

        subject = self.build_subject(request)
        body = self.build_body(request)
        html_body = self.build_html(request)

        delivery = self._sender.send(
            request,
            subject=subject,
            body=body,
            html_body=html_body,
        )

        if inspect.isawaitable(delivery):
            return replace(
                request,
                delivery=delivery,
            )

        return request


def _build_html(
    request: PlatformIntelligenceEscalationEmailRequest,
    frontend_base_url: str,
) -> str:
    import html

    def esc(value: object) -> str:
        return html.escape(str(value))

    def items(values: tuple[str, ...]) -> str:
        return "".join(
            f"<li>{esc(value)}</li>"
            for value in values
        )

    review_url = request.review_url

    if not review_url and frontend_base_url:
        review_url = (
            f"{frontend_base_url}"
            "/operations-center/compliance/reviews"
            f"?review_item_id={request.review_item_id}"
        )

    review_block = (
        f'<p><a href="{esc(review_url)}">'
        "Open Platform Intelligence Review"
        "</a></p>"
        if review_url
        else ""
    )

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Platform Intelligence Escalation</title>
</head>
<body style="font-family:Arial,sans-serif;line-height:1.5;color:#172033;background:#f5f7fb;padding:24px;">
  <div style="max-width:680px;margin:0 auto;background:#fff;border:1px solid #dfe5ef;border-radius:14px;padding:28px;">
    <p style="font-size:12px;font-weight:700;letter-spacing:.12em;color:#64748b;">
      EASYWORLD · PLATFORM INTELLIGENCE
    </p>

    <h1 style="font-size:24px;margin:8px 0 6px;">
      Human Escalation Review Required
    </h1>

    <p>
      A governed Platform Intelligence escalation recommendation
      has been generated.
    </p>

    <p>
      <strong>This is a recommendation for human review only.</strong>
      It does not constitute approval, rejection, remediation
      authorization, or production action.
    </p>

    <h2 style="font-size:16px;">Risk</h2>
    <ul>
      <li><strong>Scope:</strong> {esc(request.scope)}</li>
      <li><strong>Risk level:</strong> {esc(request.risk_level)}</li>
      <li><strong>Risk score:</strong> {request.risk_score:.4f}</li>
      <li><strong>Escalation route:</strong> {esc(request.route)}</li>
    </ul>

    <h2 style="font-size:16px;">Traceability</h2>
    <ul>
      <li><strong>Recommendation:</strong> {esc(request.recommendation_id)}</li>
      <li><strong>Risk decision:</strong> {esc(request.risk_decision_id)}</li>
      <li><strong>Review item:</strong> {esc(request.review_item_id)}</li>
      <li><strong>Generated:</strong> {esc(request.generated_at)}</li>
    </ul>

    <h2 style="font-size:16px;">Governance</h2>
    <ul>
      <li><strong>Quality gate:</strong> {esc(request.quality_gate_status)}</li>
      <li><strong>Review status:</strong> {esc(request.review_status)}</li>
      <li><strong>Decision status:</strong> {esc(request.decision_status)}</li>
      <li><strong>Policy:</strong> {esc(request.policy_id)} / {esc(request.policy_version)}</li>
    </ul>

    <h2 style="font-size:16px;">Escalation Reasons</h2>
    <ul>{items(request.reasons)}</ul>

    <h2 style="font-size:16px;">Evidence References</h2>
    <ul>{items(request.evidence_references)}</ul>

    <h2 style="font-size:16px;">Historical References</h2>
    <ul>{items(request.historical_references)}</ul>

    <h2 style="font-size:16px;">Assessment Rationale</h2>
    <p>{esc(request.rationale)}</p>

    <h2 style="font-size:16px;">Action Required</h2>
    <p>
      Open the authoritative Platform Intelligence review record
      and complete the human review in the controlled system.
      Do not approve, reject, or authorize remediation from the
      email itself. Any SLA or response target is governed by the
      authoritative review record and escalation policy.
    </p>

    <h2 style="font-size:16px;">Decision Control</h2>
    <p>
      Email reply does not constitute acceptance, rejection,
      or authorization.
    </p>

    {review_block}
  </div>
</body>
</html>"""


__all__ = [
    "PlatformIntelligenceEscalationEmailRequest",
    "PlatformIntelligenceEscalationEmailSender",
    "PlatformIntelligenceEscalationEmailService",
]