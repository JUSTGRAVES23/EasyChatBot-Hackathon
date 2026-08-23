"""
Build YETI governance context for cybersecurity email notifications.

This module does not send email and does not modify governance state.
"""

from __future__ import annotations

from typing import Any

from backend.cybersecurity.governance.yeti_governance_service import (
    YetiGovernanceService,
)


def build_yeti_email_context(
    report: dict[str, Any],
) -> dict[str, str]:
    """Create the YETI explanation that can be rendered by the email layer."""

    if not isinstance(report, dict):
        raise TypeError("report must be a dictionary.")

    critical = int(report.get("critical_count", 0))
    high = int(report.get("high_count", 0))

    event = {
        "event": report.get(
            "governance_event",
            (
                "SECURITY_INCIDENT"
                if critical
                else "GOVERNANCE_EVENT"
            ),
        ),
        "component": report.get(
            "governance_component",
            "Cybersecurity",
        ),
        "reason": report.get(
            "governance_reason",
            report.get(
                "posture",
                "Cybersecurity posture requires review.",
            ),
        ),
        "actor": report.get(
            "governance_actor",
            "Cybersecurity monitoring",
        ),
        "severity": (
            "critical"
            if critical > 0
            else "warning"
            if high > 0
            else "info"
        ),
    }

    explanation = YetiGovernanceService().explain(event)

    return {
        "title": explanation.title,
        "summary": explanation.summary,
        "interpretation": explanation.interpretation,
        "authority": explanation.authority,
        "action_required": explanation.action_required,
    }
