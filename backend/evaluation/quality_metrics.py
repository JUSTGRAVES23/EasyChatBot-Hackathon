"""
AI Quality Metrics.

Defines measurable evaluation dimensions.
"""


from dataclasses import dataclass


@dataclass(frozen=True)
class QualityMetrics:
    """
    AI response quality dimensions.
    """

    relevance: float

    clarity: float

    safety: float

    personalisation: float