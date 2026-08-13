"""
Preference Understanding Skill.

Transforms explicit learner discovery intent and approved preference
context into a bounded DiscoveryProfile.

The Skill is intentionally deterministic for Beta 1.

It does not:
- call an LLM
- search the web
- call product/content providers
- persist preferences
- modify memory
- infer sensitive attributes
- perform external actions

Preference sources are supplied by the owning Discovery Agent through
SkillInput.metadata. The Skill does not access repositories directly.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from backend.skills.skill import Skill, SkillInput
from backend.skills.skill_result import SkillResult
from backend.skills.discovery.preference_source import (
    PreferenceContext,
)


@dataclass(frozen=True)
class DiscoveryProfile:
    """
    Bounded profile used by the Discovery Agent.

    Explicit learner instructions are represented separately from
    approved contextual preferences so downstream Skills can apply
    appropriate precedence.
    """

    topics: tuple[str, ...] = ()
    content_types: tuple[str, ...] = ()
    languages: tuple[str, ...] = ()
    learning_level: str | None = None
    explicit_constraints: tuple[str, ...] = ()

    @property
    def is_empty(self) -> bool:
        """Return whether the profile contains no discovery signals."""
        return not any(
            (
                self.topics,
                self.content_types,
                self.languages,
                self.learning_level,
                self.explicit_constraints,
            )
        )

    def as_dict(self) -> dict[str, object]:
        """Return a serialisable representation."""
        return {
            "topics": list(self.topics),
            "content_types": list(self.content_types),
            "languages": list(self.languages),
            "learning_level": self.learning_level,
            "explicit_constraints": list(
                self.explicit_constraints
            ),
        }


class PreferenceUnderstandingSkill(Skill):
    """
    Extracts bounded discovery preferences from:

    1. the learner's current explicit request
    2. approved PreferenceContext supplied by the Discovery Agent

    Current explicit requests have precedence over contextual defaults.

    The Skill does not retrieve memory or usage data itself.
    """

    skill_id = "discovery.preference_understanding"
    name = "Preference Understanding"
    version = "1.1.0"

    _CONTENT_TYPES: tuple[tuple[str, str], ...] = (
        ("podcasts", "podcast"),
        ("podcast", "podcast"),
        ("news", "news"),
        ("articles", "article"),
        ("article", "article"),
        ("products", "product"),
        ("product", "product"),
    )

    _LANGUAGES: tuple[str, ...] = (
        "english",
        "french",
        "spanish",
        "german",
        "italian",
        "portuguese",
        "russian",
        "dutch",
    )

    _LEVEL_PATTERN = re.compile(
        r"\b(?:A1|A2|B1|B2|C1|C2)\b",
        re.IGNORECASE,
    )

    async def execute(
        self,
        skill_input: SkillInput,
    ) -> SkillResult:
        """
        Build a bounded DiscoveryProfile.

        Approved PreferenceContext is read from:

            skill_input.metadata["preference_context"]

        The generic SkillInput contract therefore remains independent
        from the Discovery workstream.
        """

        if skill_input is None:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error="Skill input cannot be None.",
            )

        if not isinstance(skill_input.request, str):
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

        preference_context = (
            self._get_preference_context(
                skill_input.metadata
            )
        )

        try:
            profile = self._build_profile(
                request=request,
                preference_context=preference_context,
            )
        except ValueError as exc:
            return SkillResult.failed(
                skill_id=self.skill_id,
                error=str(exc),
            )

        return SkillResult.succeeded(
            skill_id=self.skill_id,
            output=profile,
        )

    def _get_preference_context(
        self,
        metadata: dict[str, object],
    ) -> PreferenceContext | None:
        """
        Retrieve the approved PreferenceContext from Skill metadata.

        Missing preference context is valid for the hackathon because
        discovery must remain functional without learner-memory access.
        """

        value = metadata.get(
            "preference_context"
        )

        if value is None:
            return None

        if not isinstance(
            value,
            PreferenceContext,
        ):
            raise ValueError(
                "preference_context must be a PreferenceContext."
            )

        return value

    def _build_profile(
        self,
        *,
        request: str,
        preference_context: PreferenceContext | None,
    ) -> DiscoveryProfile:
        """
        Build the profile using deterministic extraction.

        Precedence:

        Current request
            ↓
        Explicit learner requirements

        Approved preference context
            ↓
        Contextual defaults

        The current request is therefore never silently overridden by
        onboarding preferences.
        """

        request_lower = request.lower()

        # ---------------------------------------------------------
        # Contextual defaults from the approved preference source
        # ---------------------------------------------------------

        topics: list[str] = []

        content_types: list[str] = []

        languages: list[str] = []

        learning_level: str | None = None

        if preference_context is not None:
            topics = list(
                preference_context.topics
            )

            content_types = (
                self._normalise_content_types(
                    preference_context.content_types
                )
            )

            languages = list(
                preference_context.languages
            )

            learning_level = (
                preference_context.learning_level
            )

        # ---------------------------------------------------------
        # Explicit current request
        # ---------------------------------------------------------

        explicit_content_types = (
            self._extract_content_types(
                request_lower
            )
        )

        explicit_languages = (
            self._extract_languages(
                request_lower
            )
        )

        explicit_learning_level = (
            self._extract_learning_level(
                request
            )
        )

        explicit_topics = self._extract_topics(
            request=request,
            request_lower=request_lower,
            content_types=explicit_content_types,
        )

        explicit_constraints = (
            self._extract_constraints(
                request=request,
                request_lower=request_lower,
            )
        )

        # Explicit request values are placed first.
        content_types = self._merge_unique(
            explicit_content_types,
            content_types,
        )

        languages = self._merge_unique(
            explicit_languages,
            languages,
        )

        topics = self._merge_unique(
            explicit_topics,
            topics,
        )

        if explicit_learning_level is not None:
            learning_level = (
                explicit_learning_level
            )

        return DiscoveryProfile(
            topics=tuple(topics),
            content_types=tuple(content_types),
            languages=tuple(languages),
            learning_level=learning_level,
            explicit_constraints=tuple(
                explicit_constraints
            ),
        )

    @staticmethod
    def _normalise_content_types(
        values: Iterable[str],
    ) -> list[str]:
        """
        Convert supported content-type vocabulary into the
        canonical DiscoveryProfile representation.

        Canonical values:
        - podcast
        - news
        - article
        - product

        Normalisation occurs at the Skill boundary so downstream
        Discovery Skills can rely on one stable vocabulary.
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
            if not isinstance(value, str):
                continue

            normalised = value.strip().lower()

            canonical = aliases.get(normalised)

            if (
                canonical is not None
                and canonical not in result
            ):
                result.append(canonical)

        return result

    def _extract_content_types(
        self,
        request_lower: str,
    ) -> list[str]:
        return self._merge_unique(
            [],
            [
                normalised
                for marker, normalised
                in self._CONTENT_TYPES
                if re.search(
                    rf"\b{re.escape(marker)}\b",
                    request_lower,
                )
            ],
        )

    def _extract_languages(
        self,
        request_lower: str,
    ) -> list[str]:
        return self._merge_unique(
            [],
            [
                language
                for language in self._LANGUAGES
                if re.search(
                    rf"\b{re.escape(language)}\b",
                    request_lower,
                )
            ],
        )

    def _extract_learning_level(
        self,
        request: str,
    ) -> str | None:
        match = self._LEVEL_PATTERN.search(
            request
        )

        return (
            match.group(0).upper()
            if match
            else None
        )

    def _extract_topics(
        self,
        *,
        request: str,
        request_lower: str,
        content_types: Iterable[str],
    ) -> list[str]:
        """
        Extract obvious topic phrases without broad semantic inference.
        """

        patterns = (
            r"\babout\s+(.+?)(?=\s+(?:in|for|on)\s+\w+|$)",
            r"\b(?:on|around)\s+(.+?)(?=\s+(?:in|for)\s+\w+|$)",
        )

        topics: list[str] = []

        for pattern in patterns:
            match = re.search(
                pattern,
                request_lower,
            )

            if match:
                candidate = self._clean_topic(
                    match.group(1)
                )

                if candidate:
                    topics.append(candidate)

        if (
            "artificial intelligence"
            in request_lower
            or re.search(
                r"\bai\b",
                request_lower,
            )
        ):
            topics.append(
                "artificial intelligence"
            )

        if "machine learning" in request_lower:
            topics.append(
                "machine learning"
            )

        return self._merge_unique(
            [],
            topics,
        )

    def _extract_constraints(
        self,
        *,
        request: str,
        request_lower: str,
    ) -> list[str]:
        constraints: list[str] = []

        for pattern in (
            r"\b(?:only|just)\s+(.+?)(?:[.!?]|$)",
            r"\bwithout\s+(.+?)(?:[.!?]|$)",
        ):
            for match in re.finditer(
                pattern,
                request_lower,
            ):
                candidate = (
                    self._clean_constraint(
                        match.group(1)
                    )
                )

                if candidate:
                    constraints.append(
                        candidate
                    )

        return self._merge_unique(
            [],
            constraints,
        )

    @staticmethod
    def _clean_topic(
        value: str,
    ) -> str:
        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip(
            " ,.;:!?"
        )

        return (
            value
            if 2 <= len(value) <= 100
            else ""
        )

    @staticmethod
    def _clean_constraint(
        value: str,
    ) -> str:
        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip(
            " ,.;:!?"
        )

        return (
            value
            if 2 <= len(value) <= 120
            else ""
        )

    @staticmethod
    def _merge_unique(
        existing: list[str],
        values: Iterable[str],
    ) -> list[str]:
        result = list(existing)

        for value in values:
            if value and value not in result:
                result.append(value)

        return result