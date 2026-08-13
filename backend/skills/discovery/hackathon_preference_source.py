"""
Hackathon Preference Source.

Provides Discovery preferences from the EasyChatBot onboarding
questionnaire.

This implementation deliberately does not depend on the future
platform Memory repository.

The interface is designed so it can later be replaced by a
production PlatformPreferenceSource without changing Discovery Skills.
"""

from __future__ import annotations

from collections.abc import Mapping

from backend.skills.discovery.preference_source import (
    PreferenceContext,
)


class HackathonPreferenceSource:
    """
    In-memory onboarding preference source for the hackathon.

    The application can initialise this source with the answers
    collected during onboarding.
    """

    def __init__(
        self,
        preferences: Mapping[str, object] | None = None,
    ) -> None:
        self._preferences = dict(
            preferences or {}
        )

    async def get_preferences(
        self,
        user_id: str,
    ) -> PreferenceContext:
        """
        Return onboarding preferences for the learner.

        The hackathon implementation stores only the explicitly
        supplied onboarding data.
        """

        if not isinstance(user_id, str):
            raise ValueError(
                "user_id must be a string."
            )

        if not user_id.strip():
            raise ValueError(
                "user_id cannot be empty."
            )

        return PreferenceContext(
            topics=self._normalise_values(
                self._preferences.get("topics")
            ),
            content_types=self._normalise_values(
                self._preferences.get("content_types")
            ),
            languages=self._normalise_values(
                self._preferences.get("languages")
            ),
            learning_level=self._normalise_level(
                self._preferences.get(
                    "learning_level"
                )
            ),
            source="onboarding",
            metadata={
                "repository": "hackathon",
                "preference_source": "onboarding_questionnaire",
            },
        )

    @staticmethod
    def _normalise_values(
        value: object,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        if isinstance(value, str):
            values = [value]
        elif isinstance(value, (list, tuple, set)):
            values = value
        else:
            raise ValueError(
                "Preference values must be strings or collections "
                "of strings."
            )

        result: list[str] = []

        for item in values:
            if not isinstance(item, str):
                raise ValueError(
                    "Preference values must contain strings only."
                )

            normalised = item.strip().lower()

            if normalised and normalised not in result:
                result.append(normalised)

        return tuple(result)

    @staticmethod
    def _normalise_level(
        value: object,
    ) -> str | None:
        if value is None:
            return None

        if not isinstance(value, str):
            raise ValueError(
                "learning_level must be a string."
            )

        level = value.strip().upper()

        if level not in {
            "A1",
            "A2",
            "B1",
            "B2",
            "C1",
            "C2",
        }:
            raise ValueError(
                "learning_level must be A1, A2, B1, B2, C1, or C2."
            )

        return level