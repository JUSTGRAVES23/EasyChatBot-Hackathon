"""
Discovery Query Generation Skill.

Generates bounded, provider-independent discovery queries from
validated learner preferences and the current discovery request.

The Skill is intentionally deterministic for Beta 1.

It does not:
- call an LLM
- call search providers
- call product providers
- access memory repositories
- persist preferences
- perform external actions
- contain provider-specific search syntax

Responsibilities:

- consume the canonical DiscoveryProfile
- preserve explicit learner constraints
- generate queries for supported discovery types
- incorporate topics, languages and learning level
- produce bounded provider-independent search intent

Architecture:

PreferenceUnderstandingSkill
        |
        v
DiscoveryProfile
        |
        v
DiscoveryQueryGenerationSkill
        |
        v
DiscoveryQuery[]
        |
        v
Content/Product Discovery
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from skills.discovery.preference_understanding import (
    DiscoveryProfile,
)
from skills.skill import (
    Skill,
    SkillInput,
)
from skills.skill_result import (
    SkillResult,
)


@dataclass(frozen=True)
class DiscoveryQuery:
    """
    Provider-independent discovery query.

    Attributes
    ----------
    query:
        Human-readable search intent.

    content_type:
        Canonical discovery type.

    topics:
        Topics represented by the query.

    languages:
        Languages represented by the query.

    learning_level:
        Optional learner level.

    constraints:
        Explicit learner constraints that must be preserved.
    """

    query: str
    content_type: str
    topics: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    learning_level: str | None = None
    constraints: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""
        return {
            "query": self.query,
            "content_type": self.content_type,
            "topics": list(self.topics),
            "languages": list(self.languages),
            "learning_level": self.learning_level,
            "constraints": list(self.constraints),
        }


class DiscoveryQueryGenerationSkill(Skill):
    """
    Generate bounded discovery queries.

    The Skill consumes a DiscoveryProfile supplied through
    SkillInput.metadata.

    Expected metadata:

        {
            "discovery_profile": DiscoveryProfile(...)
        }

    The current request remains available through SkillInput.request
    and is preserved as the primary learner intent.
    """

    skill_id = "discovery.query_generation"
    name = "Discovery Query Generation"
    version = "1.0.0"

    _SUPPORTED_CONTENT_TYPES = (
        "podcast",
        "news",
        "article",
        "product",
    )

    _MAX_QUERIES = 8

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Generate provider-independent discovery queries.
        """

        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        if not isinstance(
            skill_input.request,
            str,
        ):
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill request must be a string.",
            )

        request = skill_input.request.strip()

        if not request:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill request cannot be empty.",
            )

        try:
            profile = self._get_profile(
                skill_input.metadata
            )
        except ValueError as exc:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=str(exc),
            )

        queries = self._generate_queries(
            request=request,
            profile=profile,
        )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=queries,
        )

    def _get_profile(
        self,
        metadata: dict[str, object],
    ) -> DiscoveryProfile:
        """
        Retrieve the validated DiscoveryProfile.

        Query Generation does not construct or retrieve preferences.
        PreferenceUnderstandingSkill owns that responsibility.
        """

        value = metadata.get(
            "discovery_profile"
        )

        if value is None:
            raise ValueError(
                "discovery_profile is required."
            )

        if not isinstance(
            value,
            DiscoveryProfile,
        ):
            raise ValueError(
                "discovery_profile must be a DiscoveryProfile."
            )

        return value

    def _generate_queries(
        self,
        *,
        request: str,
        profile: DiscoveryProfile,
    ) -> tuple[DiscoveryQuery, ...]:
        """
        Generate bounded queries.

        Explicit content types are used when available.

        If no content type is available, the query is represented
        as a general discovery query using the first supported
        discovery type: article.

        This fallback keeps the Skill usable without silently
        inventing multiple discovery channels.
        """

        content_types = self._normalise_content_types(
            profile.content_types
        )

        if not content_types:
            content_types = ["article"]

        topics = self._normalise_values(
            profile.topics
        )

        languages = self._normalise_values(
            profile.languages
        )

        constraints = self._normalise_values(
            profile.explicit_constraints
        )

        generated: list[DiscoveryQuery] = []

        for content_type in content_types:
            query = self._build_query(
                request=request,
                content_type=content_type,
                topics=topics,
                languages=languages,
                learning_level=profile.learning_level,
                constraints=constraints,
            )

            generated.append(
                DiscoveryQuery(
                    query=query,
                    content_type=content_type,
                    topics=tuple(topics),
                    languages=tuple(languages),
                    learning_level=profile.learning_level,
                    constraints=tuple(constraints),
                )
            )

            if len(generated) >= self._MAX_QUERIES:
                break

        return tuple(generated)

    def _build_query(
        self,
        *,
        request: str,
        content_type: str,
        topics: list[str],
        languages: list[str],
        learning_level: str | None,
        constraints: list[str],
    ) -> str:
        """
        Build a human-readable provider-independent query.

        The current request is retained as the primary intent.
        Profile information enriches it rather than replacing it.
        """

        parts: list[str] = [
            request
        ]

        if topics:
            parts.append(
                "Topics: "
                + ", ".join(topics)
            )

        parts.append(
            f"Content type: {content_type}"
        )

        if languages:
            parts.append(
                "Language: "
                + ", ".join(languages)
            )

        if learning_level:
            parts.append(
                "Learning level: "
                + learning_level
            )

        if constraints:
            parts.append(
                "Constraints: "
                + "; ".join(constraints)
            )

        return " | ".join(parts)

    @classmethod
    def _normalise_content_types(
        cls,
        values: Iterable[str],
    ) -> list[str]:
        """
        Convert supported content-type aliases into canonical values.
        """

        aliases = {
            "podcast": "podcast",
            "podcasts": "podcast",
            "news": "news",
            "article": "article",
            "articles": "article",
            "product": "product",
            "products": "product",
        }

        result: list[str] = []

        for value in values:
            if not isinstance(
                value,
                str,
            ):
                continue

            canonical = aliases.get(
                value.strip().lower()
            )

            if (
                canonical is not None
                and canonical not in result
            ):
                result.append(canonical)

        return [
            value
            for value in result
            if value in cls._SUPPORTED_CONTENT_TYPES
        ]

    @staticmethod
    def _normalise_values(
        values: Iterable[str],
    ) -> list[str]:
        """
        Normalise bounded textual preference values.
        """

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
