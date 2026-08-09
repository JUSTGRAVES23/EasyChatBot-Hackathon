"""
AI Evaluation Domain Models.

Defines provider-independent contracts for evaluating
EasyChatBot AI outputs.

Architecture:

AI Output
    |
    v
Evaluation Engine
    |
    v
Evaluation Result

This module contains domain models only.

It must not:
- call an LLM
- call an external provider
- execute agents
- modify application data
- depend on the Conversation Agent
"""

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class EvaluationCriterion:
    """
    Defines one quality criterion.
    """

    name: str
    description: str
    weight: float = 1.0


@dataclass(frozen=True)
class CriterionScore:
    """
    Score assigned to one evaluation criterion.
    """

    criterion: str
    score: float
    reasoning: str


@dataclass(frozen=True)
class EvaluationResult:
    """
    Complete evaluation result for an AI output.
    """

    overall_score: float
    scores: List[CriterionScore]
    passed: bool
    evaluator: str = "deterministic"