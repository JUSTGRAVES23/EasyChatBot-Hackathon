"""
Tests for AI Governance Policy Engine.
"""

from src.governance.engine import (
    GovernancePolicyEngine,
)

from src.governance.models import (
    GovernanceDecision,
    GovernancePolicy,
    RiskLevel,
)


def test_low_risk_capability_is_allowed():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        GovernancePolicy(
            capability="content_formatting",
            risk_level=RiskLevel.LOW,
        )
    )

    assert result.decision == GovernanceDecision.ALLOW
    assert result.risk_level == RiskLevel.LOW


def test_external_research_can_be_allowed():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        GovernancePolicy(
            capability="live_web_research",
            risk_level=RiskLevel.MEDIUM,
            allows_external_calls=True,
        )
    )

    assert result.decision == GovernanceDecision.ALLOW

    assert any(
        "External calls" in reason
        for reason in result.reasons
    )


def test_human_review_policy_requires_review():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        GovernancePolicy(
            capability="high_impact_decision",
            risk_level=RiskLevel.MEDIUM,
            requires_human_review=True,
        )
    )

    assert result.decision == GovernanceDecision.REVIEW


def test_high_risk_capability_requires_review():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        GovernancePolicy(
            capability="high_risk_operation",
            risk_level=RiskLevel.HIGH,
        )
    )

    assert result.decision == GovernanceDecision.REVIEW


def test_critical_risk_is_blocked():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        GovernancePolicy(
            capability="critical_operation",
            risk_level=RiskLevel.CRITICAL,
        )
    )

    assert result.decision == GovernanceDecision.BLOCK


def test_side_effects_are_blocked():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        GovernancePolicy(
            capability="external_modification",
            risk_level=RiskLevel.MEDIUM,
            allows_side_effects=True,
        )
    )

    assert result.decision == GovernanceDecision.BLOCK

    assert (
        "Uncontrolled side effects are prohibited."
        in result.reasons
    )


def test_side_effect_block_takes_precedence_over_review():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        GovernancePolicy(
            capability="dangerous_operation",
            risk_level=RiskLevel.HIGH,
            requires_human_review=True,
            allows_side_effects=True,
        )
    )

    assert result.decision == GovernanceDecision.BLOCK


def test_critical_risk_takes_precedence_over_review():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        GovernancePolicy(
            capability="critical_operation",
            risk_level=RiskLevel.CRITICAL,
            requires_human_review=True,
        )
    )

    assert result.decision == GovernanceDecision.BLOCK