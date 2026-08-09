"""
Tests for AI Governance domain models.
"""

from src.governance.models import (
    GovernanceDecision,
    GovernancePolicy,
    GovernanceResult,
    RiskLevel,
)


def test_governance_policy_creation():

    policy = GovernancePolicy(
        capability="live_web_research",
        risk_level=RiskLevel.MEDIUM,
        requires_human_review=False,
        allows_external_calls=True,
        allows_side_effects=False,
    )

    assert policy.capability == "live_web_research"
    assert policy.risk_level == RiskLevel.MEDIUM
    assert policy.allows_external_calls is True
    assert policy.allows_side_effects is False


def test_governance_result_creation():

    result = GovernanceResult(
        capability="live_web_research",
        decision=GovernanceDecision.ALLOW,
        risk_level=RiskLevel.MEDIUM,
        reasons=("External research is permitted.",),
    )

    assert result.capability == "live_web_research"
    assert result.decision == GovernanceDecision.ALLOW
    assert result.risk_level == RiskLevel.MEDIUM
    assert len(result.reasons) == 1


def test_risk_levels_are_defined():

    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.MEDIUM.value == "medium"
    assert RiskLevel.HIGH.value == "high"
    assert RiskLevel.CRITICAL.value == "critical"


def test_governance_decisions_are_defined():

    assert GovernanceDecision.ALLOW.value == "allow"
    assert GovernanceDecision.REVIEW.value == "review"
    assert GovernanceDecision.BLOCK.value == "block"


def test_governance_policy_is_immutable():

    policy = GovernancePolicy(
        capability="test",
        risk_level=RiskLevel.LOW,
    )

    try:
        policy.capability = "changed"
        assert False
    except AttributeError:
        assert True


def test_governance_result_is_immutable():

    result = GovernanceResult(
        capability="test",
        decision=GovernanceDecision.ALLOW,
        risk_level=RiskLevel.LOW,
        reasons=(),
    )

    try:
        result.decision = GovernanceDecision.BLOCK
        assert False
    except AttributeError:
        assert True