"""
Sprint H3 — AI Governance Demo.

Demonstrates the EasyChatBot governance decision model:

Capability
        ↓
Governance Policy
        ↓
Governance Policy Engine
        ↓
ALLOW / REVIEW / BLOCK

This demo is deterministic and does not:
- call an LLM
- call Parallel
- execute an agent
- modify external systems
"""

from __future__ import annotations

import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Repository path bootstrap
# ---------------------------------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]

if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))


from src.governance.engine import (
    GovernancePolicyEngine,
)

from src.governance.models import (
    GovernanceDecision,
    GovernancePolicy,
    RiskLevel,
)


def run_demo() -> None:
    """
    Demonstrate the governance policy engine.
    """

    print()
    print("=" * 64)
    print("EasyChatBot — Sprint H3")
    print("AI Safety & Governance Demo")
    print("=" * 64)
    print()

    engine = GovernancePolicyEngine()

    scenarios = [
        GovernancePolicy(
            capability="content_formatting",
            risk_level=RiskLevel.LOW,
            requires_human_review=False,
            allows_external_calls=False,
            allows_side_effects=False,
        ),
        GovernancePolicy(
            capability="live_intelligence_research",
            risk_level=RiskLevel.MEDIUM,
            requires_human_review=False,
            allows_external_calls=True,
            allows_side_effects=False,
        ),
        GovernancePolicy(
            capability="high_risk_decision_support",
            risk_level=RiskLevel.HIGH,
            requires_human_review=False,
            allows_external_calls=True,
            allows_side_effects=False,
        ),
        GovernancePolicy(
            capability="critical_operation",
            risk_level=RiskLevel.CRITICAL,
            requires_human_review=False,
            allows_external_calls=True,
            allows_side_effects=False,
        ),
        GovernancePolicy(
            capability="external_system_modification",
            risk_level=RiskLevel.MEDIUM,
            requires_human_review=False,
            allows_external_calls=True,
            allows_side_effects=True,
        ),
    ]

    for index, policy in enumerate(
        scenarios,
        start=1,
    ):
        result = engine.evaluate(policy)

        print(f"SCENARIO {index}")
        print("-" * 64)
        print(f"Capability: {result.capability}")
        print(f"Risk level: {result.risk_level.value}")
        print(
            "External calls: "
            f"{policy.allows_external_calls}"
        )
        print(
            "Side effects: "
            f"{policy.allows_side_effects}"
        )
        print(
            "Human review: "
            f"{policy.requires_human_review}"
        )
        print(
            f"Decision: {result.decision.value.upper()}"
        )

        print("Reasons:")

        for reason in result.reasons:
            print(f"  • {reason}")

        print()

    print("=" * 64)
    print("Governance decision model demonstrated.")
    print("=" * 64)
    print()

    # Explicit assertions make the demo itself a useful
    # executable smoke test.

    decisions = [
        engine.evaluate(policy).decision
        for policy in scenarios
    ]

    assert decisions == [
        GovernanceDecision.ALLOW,
        GovernanceDecision.ALLOW,
        GovernanceDecision.REVIEW,
        GovernanceDecision.BLOCK,
        GovernanceDecision.BLOCK,
    ]


def main() -> None:
    """
    Application entry point.
    """

    run_demo()


if __name__ == "__main__":
    main()