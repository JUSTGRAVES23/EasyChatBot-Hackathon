"""
Quality Evaluation Result.

Represents the output of internal
AI quality analysis.
"""


from dataclasses import dataclass


@dataclass(frozen=True)
class QualityResult:
    """
    Result produced by Quality Agent.
    """

    score: float

    passed: bool

    findings: list[str]

    recommendations: list[str]