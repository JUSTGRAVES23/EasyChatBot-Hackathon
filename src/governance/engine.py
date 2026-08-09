"""
AI Governance Policy Engine.

Applies explicit governance policies to AI capabilities.

Architecture:

Capability Request
        |
        v
Governance Policy Engine
        |
        v
Governance Result

Decision model:
- ALLOW   → capability is permitted
- REVIEW  → human review is required
- BLOCK   → capability is prohibited

This module does not:
- execute agents
- call LLMs
- call external providers
- modify application state
- perform external side effects
"""

from src.governance.models import (
    GovernanceDecision,
    GovernancePolicy,
    GovernanceResult,
    RiskLevel,
)


class GovernancePolicyEngine:
    """
    Deterministic governance decision engine.
    """

    def evaluate(
        self,
        policy: GovernancePolicy,
    ) -> GovernanceResult:
        """
        Evaluate a governance policy.

        Decision precedence:

        1. Side effects are blocked by default.
        2. Critical risk requires blocking.
        3. Explicit human review requires REVIEW.
        4. Otherwise the capability is ALLOWED.
        """

        reasons: list[str] = []

        # ---------------------------------------------------------
        # Side effects
        # ---------------------------------------------------------

        if policy.allows_side_effects:
            return GovernanceResult(
                capability=policy.capability,
                decision=GovernanceDecision.BLOCK,
                risk_level=policy.risk_level,
                reasons=(
                    "Uncontrolled side effects are prohibited.",
                ),
            )

        # ---------------------------------------------------------
        # Critical risk
        # ---------------------------------------------------------

        if policy.risk_level == RiskLevel.CRITICAL:
            return GovernanceResult(
                capability=policy.capability,
                decision=GovernanceDecision.BLOCK,
                risk_level=policy.risk_level,
                reasons=(
                    "Critical-risk capabilities require "
                    "stronger controls than this policy permits.",
                ),
            )

        # ---------------------------------------------------------
        # High-risk operations
        # ---------------------------------------------------------

        if policy.risk_level == RiskLevel.HIGH:
            reasons.append(
                "High-risk capability requires human review."
            )

            return GovernanceResult(
                capability=policy.capability,
                decision=GovernanceDecision.REVIEW,
                risk_level=policy.risk_level,
                reasons=tuple(reasons),
            )

        # ---------------------------------------------------------
        # Explicit human review
        # ---------------------------------------------------------

        if policy.requires_human_review:
            reasons.append(
                "Policy explicitly requires human review."
            )

            return GovernanceResult(
                capability=policy.capability,
                decision=GovernanceDecision.REVIEW,
                risk_level=policy.risk_level,
                reasons=tuple(reasons),
            )

        # ---------------------------------------------------------
        # External calls
        # ---------------------------------------------------------

        if policy.allows_external_calls:
            reasons.append(
                "External calls are explicitly permitted."
            )
        else:
            reasons.append(
                "No external calls are required."
            )

        # ---------------------------------------------------------
        # Default allow
        # ---------------------------------------------------------

        reasons.append(
            "No blocking governance condition was detected."
        )

        return GovernanceResult(
            capability=policy.capability,
            decision=GovernanceDecision.ALLOW,
            risk_level=policy.risk_level,
            reasons=tuple(reasons),
        )