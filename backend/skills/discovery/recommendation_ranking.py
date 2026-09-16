"""
Discovery Recommendation Ranking Skill.

Ranks already-matched discovery candidates using their
relevance scores.

The Skill is deterministic for Beta 1.

It does not:

- perform discovery
- call external providers
- call LLMs
- recalculate relevance
- persist memory
- modify learner preferences

Architecture:

Discovery Candidates
        |
        v
Relevance Matching
        |
        v
RelevanceMatch[]
        |
        v
Recommendation Ranking
        |
        v
RankedRecommendation[]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from skills.discovery.relevance_matching import (
    RelevanceMatch,
)
from skills.skill import (
    Skill,
    SkillInput,
)
from skills.skill_result import (
    SkillResult,
)


@dataclass(frozen=True)
class RankedRecommendation:
    """
    A discovery candidate with its final ranking position.
    """

    match: RelevanceMatch
    rank: int

    @property
    def score(self) -> float:
        """Return the underlying relevance score."""
        return self.match.score

    @property
    def candidate(self):
        """Return the underlying discovery candidate."""
        return self.match.candidate

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "rank": self.rank,
            "score": self.score,
            "candidate": (
                self.match.candidate.as_dict()
            ),
            "matched_topics": list(
                self.match.matched_topics
            ),
            "matched_languages": list(
                self.match.matched_languages
            ),
            "matched_content_type": (
                self.match.matched_content_type
            ),
            "matched_learning_level": (
                self.match.matched_learning_level
            ),
            "matched_constraints": list(
                self.match.matched_constraints
            ),
        }


class RecommendationRankingSkill(Skill):
    """
    Rank relevance matches into an ordered recommendation list.

    Expected metadata:

        {
            "relevance_matches": [
                RelevanceMatch(...),
                ...
            ]
        }

    Optional metadata:

        {
            "recommendation_limit": 10
        }
    """

    skill_id = "discovery.recommendation_ranking"
    name = "Discovery Recommendation Ranking"
    version = "1.0.0"

    DEFAULT_LIMIT = 10
    MAX_LIMIT = 20

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Rank supplied relevance matches.
        """

        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        raw_matches = skill_input.metadata.get(
            "relevance_matches"
        )

        if raw_matches is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "relevance_matches are required."
                ),
            )

        if not isinstance(
            raw_matches,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "relevance_matches must be "
                    "a list or tuple."
                ),
            )

        matches = [
            match
            for match in raw_matches
            if isinstance(
                match,
                RelevanceMatch,
            )
        ]

        limit = self._resolve_limit(
            skill_input.metadata.get(
                "recommendation_limit"
            )
        )

        ranked_matches = self._rank(
            matches
        )

        recommendations = [
            RankedRecommendation(
                match=match,
                rank=index,
            )
            for index, match in enumerate(
                ranked_matches[:limit],
                start=1,
            )
        ]

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=recommendations,
        )

    @classmethod
    def _rank(
        cls,
        matches: Iterable[RelevanceMatch],
    ) -> list[RelevanceMatch]:
        """
        Rank matches by relevance score.

        Python's sorting is stable, so candidates with
        identical scores preserve their discovery order.
        This makes Beta 1 ranking deterministic.
        """

        return sorted(
            matches,
            key=lambda match: match.score,
            reverse=True,
        )

    @classmethod
    def _resolve_limit(
        cls,
        value,
    ) -> int:
        """
        Resolve and bound the recommendation limit.
        """

        if value is None:
            return cls.DEFAULT_LIMIT

        if isinstance(
            value,
            bool,
        ):
            return cls.DEFAULT_LIMIT

        try:
            limit = int(value)
        except (
            TypeError,
            ValueError,
        ):
            return cls.DEFAULT_LIMIT

        if limit <= 0:
            return cls.DEFAULT_LIMIT

        return min(
            limit,
            cls.MAX_LIMIT,
        )
