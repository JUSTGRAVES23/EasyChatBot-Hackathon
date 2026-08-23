"""
Cybersecurity decision support models.

These models represent human decision-support output.

They do not represent automated security actions.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionPriority:

    level: str

    score: int

    rationale: str



@dataclass(frozen=True)
class SecurityDecisionItem:

    signal_id: str

    title: str

    severity: str

    category: str

    affected_area: str

    confidence: float

    priority: DecisionPriority

    decision_required: str