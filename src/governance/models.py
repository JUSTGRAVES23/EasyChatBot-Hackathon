"""
AI Governance Domain Models.

Defines provider-independent governance contracts for
EasyChatBot AI capabilities.

Architecture:

AI Capability
      |
      v
Governance Policy
      |
      v
Governance Decision

This module contains domain models only.

It must not:
- execute agents
- call LLMs
- call external providers
- modify production systems
- depend on the Conversation Agent
"""

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    """
    AI operation risk classification.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class GovernanceDecision(str, Enum):
    """
    Decision produced by governance evaluation.
    """

    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


@dataclass(frozen=True)
class GovernancePolicy:
    """
    Defines governance requirements for an AI capability.
    """

    capability: str
    risk_level: RiskLevel
    requires_human_review: bool = False
    allows_external_calls: bool = False
    allows_side_effects: bool = False


@dataclass(frozen=True)
class GovernanceResult:
    """
    Result of applying governance policy to an operation.
    """

    capability: str
    decision: GovernanceDecision
    risk_level: RiskLevel
    reasons: tuple[str, ...]