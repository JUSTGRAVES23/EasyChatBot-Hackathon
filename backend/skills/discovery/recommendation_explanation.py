"""
Discovery Recommendation Explanation Skill.

Produces concise, evidence-based explanations for ranked
recommendations.

The Skill uses only information already produced by the
discovery pipeline.

It does not:

- perform discovery
- call external providers
- call LLMs
- recalculate relevance
- change ranking
- persist memory
- modify learner preferences

Architecture:

Discovery
    |
    v
Relevance Matching
    |
    v
Recommendation Ranking
    |
    v
Recommendation Explanation
    |
    v
User-facing recommendation explanation
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.skills.discovery.recommendation_ranking import (
    RankedRecommendation,
)
from backend.skills.skill import (
    Skill,
    SkillInput,
)
from backend.skills.skill_result import (
    SkillResult,
)


@dataclass(frozen=True)
class RecommendationExplanation:
    """
    Evidence-based explanation for one recommendation.
    """

    recommendation: RankedRecommendation
    explanation: str
    reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "rank": self.recommendation.rank,
            "score": self.recommendation.score,
            "title": (
                self.recommendation.candidate.title
            ),
            "url": (
                self.recommendation.candidate.url
            ),
            "explanation": self.explanation,
            "reasons": list(self.reasons),
        }


class RecommendationExplanationSkill(Skill):
    """
    Explain why ranked recommendations match the learner.

    Expected metadata:

        {
            "ranked_recommendations": [
                RankedRecommendation(...),
                ...
            ]
        }
    """

    skill_id = "discovery.recommendation_explanation"
    name = "Discovery Recommendation Explanation"
    version = "1.0.0"

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Generate deterministic explanations.
        """

        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        raw_recommendations = (
            skill_input.metadata.get(
                "ranked_recommendations"
            )
        )

        if raw_recommendations is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "ranked_recommendations are required."
                ),
            )

        if not isinstance(
            raw_recommendations,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "ranked_recommendations must be "
                    "a list or tuple."
                ),
            )

        explanations: list[
            RecommendationExplanation
        ] = []

        for recommendation in raw_recommendations:
            if not isinstance(
                recommendation,
                RankedRecommendation,
            ):
                continue

            explanations.append(
                self._explain(
                    recommendation
                )
            )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=explanations,
        )

    @staticmethod
    def _explain(
        recommendation: RankedRecommendation,
    ) -> RecommendationExplanation:
        """
        Build an explanation strictly from existing
        relevance evidence.
        """

        match = recommendation.match
        candidate = recommendation.candidate

        reasons: list[str] = []

        if match.matched_topics:
            topics = ", ".join(
                match.matched_topics
            )

            reasons.append(
                f"matches your interests in {topics}"
            )

        if match.matched_content_type:
            reasons.append(
                f"matches your preferred "
                f"content type ({candidate.content_type})"
            )

        if match.matched_languages:
            languages = ", ".join(
                match.matched_languages
            )

            reasons.append(
                f"matches your language preference "
                f"({languages})"
            )

        if match.matched_learning_level:
            reasons.append(
                "matches your learning level"
            )

        if match.matched_constraints:
            constraints = ", ".join(
                match.matched_constraints
            )

            reasons.append(
                f"matches your constraints "
                f"({constraints})"
            )

        if not reasons:
            reasons.append(
                "was selected because it received "
                "a relevance assessment from the "
                "discovery pipeline"
            )

        explanation = (
            f"{candidate.title} was recommended because "
            + "; ".join(reasons)
            + "."
        )

        return RecommendationExplanation(
            recommendation=recommendation,
            explanation=explanation,
            reasons=tuple(reasons),
        )