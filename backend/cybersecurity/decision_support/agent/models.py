"""
Decision support output models.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DecisionBriefItem:

    title: str

    priority: str

    severity: str

    impact: str

    affected_area: str

    decision_required: str



@dataclass(frozen=True)
class CybersecurityDecisionBrief:

    executive_summary: str

    overall_priority: str

    critical_items: list[DecisionBriefItem] = field(
        default_factory=list
    )

    high_priority_items: list[DecisionBriefItem] = field(
        default_factory=list
    )

    governance_observations: list[str] = field(
        default_factory=list
    )

    trend_analysis: str = ""

    recommended_decisions: list[str] = field(
        default_factory=list
    )

    disclaimer: str = (
        "AI-generated decision support only. "
        "No automated remediation actions executed."
    )