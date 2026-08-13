"""
Discovery Personalised Content Adaptation Skill.

Adapts already-ranked recommendations to the learner's
approved discovery profile.

The Skill is deterministic for Beta 1.

It does not:

- perform discovery
- call external providers
- call LLMs
- change recommendation ranking
- modify learner preferences
- persist memory
- perform external side effects

The Skill adapts presentation and learning guidance while
preserving the original recommendation evidence.

Architecture:

Ranked Recommendation
        |
        v
Personalised Content Adaptation
        |
        v
Learner-ready Recommendation
"""

from __future__ import annotations

from dataclasses import dataclass

from backend.skills.discovery.preference_understanding import (
    DiscoveryProfile,
)
from backend.skills.discovery.recommendation_explanation import (
    RecommendationExplanation,
)
from backend.skills.skill import (
    Skill,
    SkillInput,
)
from backend.skills.skill_result import (
    SkillResult,
)


@dataclass(frozen=True)
class PersonalisedRecommendation:
    """
    Learner-adapted recommendation.

    The original recommendation remains available so
    adaptation never destroys discovery evidence.
    """

    recommendation: RecommendationExplanation
    personalised_title: str
    personalised_summary: str
    learning_suggestion: str
    adaptation_reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "rank": self.recommendation.recommendation.rank,
            "score": self.recommendation.recommendation.score,
            "title": self.personalised_title,
            "url": self.recommendation.recommendation.candidate.url,
            "summary": self.personalised_summary,
            "learning_suggestion": self.learning_suggestion,
            "explanation": self.recommendation.explanation,
            "adaptation_reasons": list(
                self.adaptation_reasons
            ),
        }


class PersonalisedContentAdaptationSkill(Skill):
    """
    Adapt recommendations to approved learner preferences.

    Expected metadata:

        {
            "discovery_profile": DiscoveryProfile(...),
            "recommendation_explanations": [
                RecommendationExplanation(...),
                ...
            ]
        }

    The Skill does not infer hidden preferences.

    Only explicit profile information is used.
    """

    skill_id = "discovery.personalised_content_adaptation"
    name = "Personalised Content Adaptation"
    version = "1.0.0"

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Adapt supplied recommendation explanations.
        """

        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        profile = skill_input.metadata.get(
            "discovery_profile"
        )

        if not isinstance(
            profile,
            DiscoveryProfile,
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="discovery_profile is required.",
            )

        raw_recommendations = (
            skill_input.metadata.get(
                "recommendation_explanations"
            )
        )

        if raw_recommendations is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "recommendation_explanations "
                    "are required."
                ),
            )

        if not isinstance(
            raw_recommendations,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "recommendation_explanations must "
                    "be a list or tuple."
                ),
            )

        recommendations: list[
            PersonalisedRecommendation
        ] = []

        for recommendation in raw_recommendations:
            if not isinstance(
                recommendation,
                RecommendationExplanation,
            ):
                continue

            recommendations.append(
                self._adapt(
                    recommendation=recommendation,
                    profile=profile,
                )
            )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=recommendations,
        )

    @staticmethod
    def _adapt(
        *,
        recommendation: RecommendationExplanation,
        profile: DiscoveryProfile,
    ) -> PersonalisedRecommendation:
        """
        Adapt one recommendation using explicit profile data.
        """

        candidate = (
            recommendation
            .recommendation
            .candidate
        )

        reasons: list[str] = []

        personalised_title = (
            candidate.title
        )

        summary = (
            candidate.description.strip()
            or "A discovery result selected for you."
        )

        if profile.learning_level:
            learning_suggestion = (
                "Explore this at your "
                f"{profile.learning_level} level."
            )

            reasons.append(
                f"adapted to learning level "
                f"{profile.learning_level}"
            )
        else:
            learning_suggestion = (
                "Explore this and decide whether "
                "it matches your current level."
            )

        if profile.languages:
            languages = ", ".join(
                profile.languages
            )

            reasons.append(
                f"considered preferred language(s): "
                f"{languages}"
            )

        if profile.topics:
            topics = ", ".join(
                profile.topics[:3]
            )

            reasons.append(
                f"focused on preferred topic(s): "
                f"{topics}"
            )

        if profile.content_types:
            content_types = ", ".join(
                profile.content_types
            )

            reasons.append(
                f"considered preferred content type(s): "
                f"{content_types}"
            )

        return PersonalisedRecommendation(
            recommendation=recommendation,
            personalised_title=personalised_title,
            personalised_summary=summary,
            learning_suggestion=learning_suggestion,
            adaptation_reasons=tuple(
                reasons
            ),
        )