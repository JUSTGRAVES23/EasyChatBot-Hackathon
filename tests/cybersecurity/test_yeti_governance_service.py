"""Tests for YETI governance interpretation."""

from cybersecurity.governance.yeti_governance_service import (
    YetiGovernanceService,
)


def test_yeti_explains_provider_pause():
    result = YetiGovernanceService().explain(
        {
            "event": "PROVIDER_PAUSED",
            "component": "Provider delivery",
            "reason": "External provider security incident",
            "actor": "Admin",
            "severity": "critical",
        }
    )

    assert result.title == "YETI â€” Governance Guardian"
    assert "paused" in result.summary.lower()
    assert "human-controlled" in result.interpretation.lower()
    assert "authorised operator" in result.action_required.lower()


def test_yeti_explains_security_incident():
    result = YetiGovernanceService().explain(
        {
            "event": "SECURITY_INCIDENT",
            "component": "Cybersecurity",
            "reason": "Critical vulnerability",
            "actor": "Cybersecurity monitoring",
            "severity": "critical",
        }
    )

    assert "security event" in result.summary.lower()
    assert "decision support only" in result.interpretation.lower()


def test_yeti_is_deterministic():
    event = {
        "event": "PROVIDER_PAUSED",
        "component": "Provider delivery",
        "reason": "Incident",
        "actor": "Admin",
        "severity": "warning",
    }

    first = YetiGovernanceService().explain(event)
    second = YetiGovernanceService().explain(event)

    assert first == second

