"""
Discovery Quality Verification Skill.

Validates recommendations before they are presented
to the learner.

The Skill is deterministic for Beta 1.

It does not:

- perform discovery
- call external providers
- call LLMs
- modify recommendation ranking
- modify learner preferences
- persist memory
- silently repair invalid data

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
Personalised Content Adaptation
    |
    v
Discovery Quality Verification
    |
    +--> approved recommendations
    |
    +--> rejected recommendations
"""

from __future__ import annotations

from dataclasses import dataclass

from skills.discovery.personalised_content_adaptation import (
    PersonalisedRecommendation,
)
from skills.skill import (
    Skill,
    SkillInput,
)
from skills.skill_result import (
    SkillResult,
)


@dataclass(frozen=True)
class QualityFinding:
    """
    A deterministic quality finding for one recommendation.
    """

    rank: int
    passed: bool
    findings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "rank": self.rank,
            "passed": self.passed,
            "findings": list(
                self.findings
            ),
        }


@dataclass(frozen=True)
class VerifiedRecommendation:
    """
    Recommendation that passed the quality gate.
    """

    recommendation: PersonalisedRecommendation
    quality: QualityFinding

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "recommendation": (
                self.recommendation.as_dict()
            ),
            "quality": (
                self.quality.as_dict()
            ),
        }


class DiscoveryQualityVerificationSkill(Skill):
    """
    Verify personalised recommendations before presentation.

    Expected metadata:

        {
            "personalised_recommendations": [
                PersonalisedRecommendation(...),
                ...
            ]
        }
    """

    skill_id = "discovery.quality_verification"
    name = "Discovery Quality Verification"
    version = "1.0.0"

    MIN_SCORE = 0.0
    MAX_SCORE = 1.0

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Verify supplied personalised recommendations.
        """

        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        raw_recommendations = (
            skill_input.metadata.get(
                "personalised_recommendations"
            )
        )

        if raw_recommendations is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "personalised_recommendations "
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
                    "personalised_recommendations must "
                    "be a list or tuple."
                ),
            )

        verified: list[
            VerifiedRecommendation
        ] = []

        rejected: list[
            QualityFinding
        ] = []

        for recommendation in raw_recommendations:
            if not isinstance(
                recommendation,
                PersonalisedRecommendation,
            ):
                continue

            finding = self._verify(
                recommendation
            )

            if finding.passed:
                verified.append(
                    VerifiedRecommendation(
                        recommendation=recommendation,
                        quality=finding,
                    )
                )
            else:
                rejected.append(
                    finding
                )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output={
                "verified": verified,
                "rejected": rejected,
                "verified_count": len(
                    verified
                ),
                "rejected_count": len(
                    rejected
                ),
            },
        )

    @classmethod
    def _verify(
        cls,
        recommendation: PersonalisedRecommendation,
    ) -> QualityFinding:
        """
        Verify one recommendation.

        No data is modified during verification.
        """

        findings: list[str] = []

        ranked = (
            recommendation
            .recommendation
            .recommendation
        )

        candidate = ranked.candidate

        # ---------------------------------------------
        # Rank
        # ---------------------------------------------

        if ranked.rank <= 0:
            findings.append(
                "Recommendation rank must be positive."
            )

        # ---------------------------------------------
        # Score
        # ---------------------------------------------

        if not (
            cls.MIN_SCORE
            <= ranked.score
            <= cls.MAX_SCORE
        ):
            findings.append(
                "Recommendation score must be "
                "between 0 and 1."
            )

        # ---------------------------------------------
        # Candidate identity
        # ---------------------------------------------

        if not candidate.title.strip():
            findings.append(
                "Recommendation title is missing."
            )

        if not candidate.url.strip():
            findings.append(
                "Recommendation URL is missing."
            )

        # ---------------------------------------------
        # Content
        # ---------------------------------------------

        if not candidate.description.strip():
            findings.append(
                "Recommendation description is missing."
            )

        if not candidate.content_type.strip():
            findings.append(
                "Recommendation content type is missing."
            )

        # ---------------------------------------------
        # Explanation
        # ---------------------------------------------

        if not recommendation.recommendation.explanation.strip():
            findings.append(
                "Recommendation explanation is missing."
            )

        # ---------------------------------------------
        # Personalised presentation
        # ---------------------------------------------

        if not recommendation.personalised_title.strip():
            findings.append(
                "Personalised title is missing."
            )

        if not recommendation.personalised_summary.strip():
            findings.append(
                "Personalised summary is missing."
            )

        if not recommendation.learning_suggestion.strip():
            findings.append(
                "Learning suggestion is missing."
            )

        return QualityFinding(
            rank=ranked.rank,
            passed=not findings,
            findings=tuple(
                findings
            ),
        )
