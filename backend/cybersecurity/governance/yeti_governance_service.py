"""
YETI Governance Explanation Service.

Read-only governance interpretation layer.
YETI explains structured governance evidence but has no control authority.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class YetiGovernanceExplanation:
    title: str
    summary: str
    interpretation: str
    authority: str
    action_required: str


class YetiGovernanceService:
    """Generate deterministic, auditable YETI explanations."""

    name = "YETI"
    role = "Governance Guardian"

    def explain(self, event: dict) -> YetiGovernanceExplanation:
        if not isinstance(event, dict):
            raise TypeError("event must be a dictionary.")

        component = str(event.get("component", "Governance")).strip()
        action = str(event.get("event", "GOVERNANCE_EVENT")).strip()
        reason = str(
            event.get("reason", "Governance event recorded.")
        ).strip()
        actor = str(
            event.get("actor", "Authorised operator")
        ).strip()
        severity = str(
            event.get("severity", "info")
        ).strip().lower()

        prefix = {
            "critical": "Critical governance attention is required.",
            "high": "High-priority governance attention is required.",
            "warning": "Governance attention is required.",
        }.get(
            severity,
            "Governance visibility is available.",
        )

        if action == "PROVIDER_PAUSED":
            summary = f"{component} is currently paused."
            interpretation = (
                "A human-controlled safeguard was activated after a governance "
                "or security concern was recorded. No automated remediation "
                "was executed by EasyChatBot."
            )
            action_required = (
                "An authorised operator should review the evidence before "
                "provider delivery is resumed."
            )

        elif action == "PROVIDER_RESUMED":
            summary = f"{component} has been resumed."
            interpretation = (
                "Provider delivery was restored through an authorised "
                "governance action. YETI does not make or execute the "
                "resume decision."
            )
            action_required = (
                "Continue monitoring the provider and retain the governance "
                "evidence for audit."
            )

        elif action in {
            "SECURITY_INCIDENT",
            "CRITICAL_SECURITY_EVENT",
        }:
            summary = "A security event requires governance attention."
            interpretation = (
                "The event has been surfaced for human review. YETI provides "
                "decision support only and does not determine remediation."
            )
            action_required = (
                "An authorised operator should assess the evidence and follow "
                "the applicable governance procedure."
            )

        elif action in {
            "APPROVAL_GRANTED",
            "CHANGE_APPROVED",
        }:
            summary = "A governance approval has been recorded."
            interpretation = (
                "The requested change passed the applicable approval step. "
                "The approval remains an auditable human governance decision."
            )
            action_required = (
                "Proceed only within the approved scope and retain the "
                "associated evidence."
            )

        else:
            summary = f"{component} recorded {action}."
            interpretation = (
                "The event is part of the governance audit trail. YETI "
                "interprets the evidence but has no control authority."
            )
            action_required = (
                "Review the event according to the applicable governance policy."
            )

        return YetiGovernanceExplanation(
            title=f"{self.name} — {self.role}",
            summary=f"{prefix} {summary}",
            interpretation=interpretation,
            authority=(
                f"Recorded action: {action}. "
                f"Actor: {actor}. Reason: {reason}"
            ),
            action_required=action_required,
        )
