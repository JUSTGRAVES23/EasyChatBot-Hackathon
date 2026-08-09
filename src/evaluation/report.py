"""
AI Evaluation Quality Report.

Transforms an EvaluationResult into a human-readable
quality report.

Architecture:

EvaluationResult
        ↓
QualityReport
        ↓
Human-readable output

This module is presentation-independent domain formatting.

It does not:
- execute agents
- call LLMs
- call external providers
- perform searches
- modify application state
"""

from src.evaluation.models import (
    CriterionScore,
    EvaluationResult,
)


class EvaluationReport:
    """
    Generates a human-readable quality report.
    """

    def generate(
        self,
        result: EvaluationResult,
    ) -> str:
        """
        Generate a text quality report.
        """

        lines: list[str] = [
            "EasyChatBot AI Quality Report",
            "=" * 32,
            "",
            f"Overall Score: {result.overall_score:.2f}",
            f"Status: {'PASS' if result.passed else 'FAIL'}",
            f"Evaluator: {result.evaluator}",
            "",
            "Criteria",
            "-" * 32,
        ]

        for score in result.scores:
            lines.extend(
                self._format_score(score)
            )

        lines.extend(
            [
                "",
                "=" * 32,
            ]
        )

        return "\n".join(lines)

    @staticmethod
    def _format_score(
        score: CriterionScore,
    ) -> list[str]:
        """
        Format one criterion score.
        """

        return [
            f"{score.criterion}: {score.score:.2f}",
            f"  {score.reasoning}",
            "",
        ]