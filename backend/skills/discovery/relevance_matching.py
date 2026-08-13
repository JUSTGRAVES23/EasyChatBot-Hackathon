"""
Discovery Relevance Matching Skill.

Evaluates how well discovered candidates match the learner's
current discovery request and approved preferences.

The Skill is deterministic for Beta 1.

It does not:

- perform discovery
- call external providers
- call LLMs
- rank recommendations globally
- persist memory
- modify learner preferences
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from backend.skills.discovery.content_product_discovery import (
    DiscoveryCandidate,
)
from backend.skills.discovery.preference_understanding import (
    DiscoveryProfile,
)
from backend.skills.skill import (
    Skill,
    SkillInput,
)
from backend.skills.skill_result import (
    SkillResult,
)


@dataclass(frozen=True)
class RelevanceMatch:
    """
    Candidate with an explainable relevance score.
    """

    candidate: DiscoveryCandidate
    score: float
    matched_topics: tuple[str, ...] = ()
    matched_languages: tuple[str, ...] = ()
    matched_content_type: bool = False
    matched_learning_level: bool = False
    matched_constraints: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""

        return {
            "candidate": self.candidate.as_dict(),
            "score": self.score,
            "matched_topics": list(
                self.matched_topics
            ),
            "matched_languages": list(
                self.matched_languages
            ),
            "matched_content_type": (
                self.matched_content_type
            ),
            "matched_learning_level": (
                self.matched_learning_level
            ),
            "matched_constraints": list(
                self.matched_constraints
            ),
        }


class RelevanceMatchingSkill(Skill):
    """
    Match discovery candidates against learner preferences.

    Expected metadata:

        {
            "discovery_profile": DiscoveryProfile(...),
            "discovery_candidates": [
                DiscoveryCandidate(...)
            ]
        }
    """

    skill_id = "discovery.relevance_matching"
    name = "Discovery Relevance Matching"
    version = "1.0.0"

    _TOPIC_WEIGHT = 0.40
    _CONTENT_TYPE_WEIGHT = 0.20
    _LANGUAGE_WEIGHT = 0.15
    _LEVEL_WEIGHT = 0.10
    _CONSTRAINT_WEIGHT = 0.15

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Evaluate all supplied discovery candidates.
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

        raw_candidates = skill_input.metadata.get(
            "discovery_candidates"
        )

        if raw_candidates is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "discovery_candidates are required."
                ),
            )

        if not isinstance(
            raw_candidates,
            (list, tuple),
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=(
                    "discovery_candidates must be "
                    "a list or tuple."
                ),
            )

        matches: list[RelevanceMatch] = []

        for candidate in raw_candidates:
            if not isinstance(
                candidate,
                DiscoveryCandidate,
            ):
                continue

            matches.append(
                self._match_candidate(
                    candidate=candidate,
                    profile=profile,
                    request=skill_input.request,
                )
            )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=matches,
        )

    def _match_candidate(
        self,
        *,
        candidate: DiscoveryCandidate,
        profile: DiscoveryProfile,
        request: str,
    ) -> RelevanceMatch:
        """
        Produce a transparent relevance assessment.
        """

        text = " ".join(
            (
                candidate.title,
                candidate.description,
            )
        ).lower()

        request_text = request.lower()

        profile_topics = self._normalise(
            profile.topics
        )

        matched_topics = tuple(
            topic
            for topic in profile_topics
            if topic.lower() in text
            or topic.lower() in request_text
        )

        # Candidate metadata is already part of the
        # provider-independent DiscoveryCandidate contract.
        #
        # Do not require a metadata_text() method on
        # DiscoveryCandidate. Relevance matching consumes
        # the existing metadata contract directly.
        metadata_text = " ".join(
            str(value)
            for value in candidate.metadata.values()
        ).lower()

        matched_languages = tuple(
            language
            for language in self._normalise(
                profile.languages
            )
            if (
                language.lower() in text
                or language.lower() in metadata_text
            )
        )

        content_type = (
            self._normalise_content_type(
                candidate.content_type
            )
        )

        expected_types = {
            self._normalise_content_type(value)
            for value in profile.content_types
        }

        matched_content_type = (
            bool(content_type)
            and content_type in expected_types
        )

        learning_level = (
            profile.learning_level
        )

        matched_learning_level = (
            learning_level is not None
            and learning_level.lower()
            in text
        )

        matched_constraints = tuple(
            constraint
            for constraint in self._normalise(
                profile.explicit_constraints
            )
            if constraint.lower() in text
        )

        score = (
            self._TOPIC_WEIGHT
            * self._ratio(
                len(matched_topics),
                len(profile_topics),
            )
            + self._CONTENT_TYPE_WEIGHT
            * float(matched_content_type)
            + self._LANGUAGE_WEIGHT
            * self._ratio(
                len(matched_languages),
                len(profile.languages),
            )
            + self._LEVEL_WEIGHT
            * float(matched_learning_level)
            + self._CONSTRAINT_WEIGHT
            * self._ratio(
                len(matched_constraints),
                len(profile.explicit_constraints),
            )
        )

        return RelevanceMatch(
            candidate=candidate,
            score=round(
                min(max(score, 0.0), 1.0),
                4,
            ),
            matched_topics=matched_topics,
            matched_languages=matched_languages,
            matched_content_type=matched_content_type,
            matched_learning_level=matched_learning_level,
            matched_constraints=matched_constraints,
        )

    @staticmethod
    def _ratio(
        matched: int,
        total: int,
    ) -> float:
        if total <= 0:
            return 0.0

        return matched / total

    @staticmethod
    def _normalise(
        values: Iterable[str],
    ) -> list[str]:
        result: list[str] = []

        for value in values:
            if not isinstance(
                value,
                str,
            ):
                continue

            normalised = " ".join(
                value.strip().split()
            )

            if (
                normalised
                and normalised not in result
            ):
                result.append(
                    normalised
                )

        return result

    @staticmethod
    def _normalise_content_type(
        value: str,
    ) -> str:
        aliases = {
            "podcasts": "podcast",
            "podcast": "podcast",
            "news": "news",
            "articles": "article",
            "article": "article",
            "products": "product",
            "product": "product",
        }

        return aliases.get(
            value.strip().lower(),
            value.strip().lower(),
        )