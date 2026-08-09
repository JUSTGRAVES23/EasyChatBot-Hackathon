"""
Integration test for H3 governance of the H1 Live Intelligence capability.

Flow:

H1 Live Intelligence Capability
        |
        v
Governance Policy
        |
        v
Governance Policy Engine
        |
        v
Governance Decision

This test validates the governance boundary only.

It does not:
- execute the Conversation Agent
- execute the Parallel API
- modify H1 implementation
- modify H2 evaluation
- perform external side effects
"""

from src.governance.engine import (
    GovernancePolicyEngine,
)

from src.governance.models import (
    GovernanceDecision,
    GovernancePolicy,
    RiskLevel,
)


def create_live_intelligence_policy() -> GovernancePolicy:
    """
    Define the governance policy for H1 Live Intelligence.

    Live research:
    - may access external information
    - must not create external side effects
    - is considered medium risk
    - does not require human approval for passive research
    """

    return GovernancePolicy(
        capability="live_intelligence_research",
        risk_level=RiskLevel.MEDIUM,
        requires_human_review=False,
        allows_external_calls=True,
        allows_side_effects=False,
    )


def test_live_intelligence_capability_is_governed():

    engine = GovernancePolicyEngine()

    policy = create_live_intelligence_policy()

    result = engine.evaluate(
        policy
    )

    assert (
        result.capability
        == "live_intelligence_research"
    )

    assert (
        result.risk_level
        == RiskLevel.MEDIUM
    )

    assert (
        result.decision
        == GovernanceDecision.ALLOW
    )


def test_live_intelligence_allows_external_research():

    engine = GovernancePolicyEngine()

    result = engine.evaluate(
        create_live_intelligence_policy()
    )

    assert any(
        "External calls are explicitly permitted."
        in reason
        for reason in result.reasons
    )


def test_live_intelligence_does_not_allow_side_effects():

    policy = create_live_intelligence_policy()

    assert policy.allows_side_effects is False


def test_live_intelligence_with_side_effects_is_blocked():

    engine = GovernancePolicyEngine()

    unsafe_policy = GovernancePolicy(
        capability="live_intelligence_research",
        risk_level=RiskLevel.MEDIUM,
        requires_human_review=False,
        allows_external_calls=True,
        allows_side_effects=True,
    )

    result = engine.evaluate(
        unsafe_policy
    )

    assert (
        result.decision
        == GovernanceDecision.BLOCK
    )


def test_live_intelligence_high_risk_requires_review():

    engine = GovernancePolicyEngine()

    high_risk_policy = GovernancePolicy(
        capability="live_intelligence_research",
        risk_level=RiskLevel.HIGH,
        requires_human_review=False,
        allows_external_calls=True,
        allows_side_effects=False,
    )

    result = engine.evaluate(
        high_risk_policy
    )

    assert (
        result.decision
        == GovernanceDecision.REVIEW
    )