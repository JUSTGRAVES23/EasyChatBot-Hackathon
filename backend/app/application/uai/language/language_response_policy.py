"""
Application policy for resolving the response language.

The active World controls whether the response language is fixed
or mirrors the user's detected language.

This component does not change the active World.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.uai.language.language_detector import (
    LanguageDetector,
)
from app.domain.uai.context.language_policy import (
    LanguagePolicy,
)

if TYPE_CHECKING:
    from app.domain.uai.context.world_context import (
        WorldContext,
    )


class LanguageResponsePolicy:
    """
    Resolve the language in which the application should respond.

    Rules
    -----
    target_language:
        Always use the World-configured target language.

    mirror_user:
        Detect the user's language and accept it only when it is
        explicitly supported by the World.

    The detector is never used for target-language Worlds.
    """

    def resolve_response_language(
        self,
        *,
        world: WorldContext,
        user_message: str,
        language_detector: LanguageDetector,
    ) -> str:
        """
        Resolve the response language for one user interaction.

        Parameters
        ----------
        world:
            Validated application-controlled WorldContext.

        user_message:
            User-provided message.

        language_detector:
            Provider-independent language detector.

        Returns
        -------
        str
            Validated response language code.

        Raises
        ------
        ValueError
            If the World has no valid language policy, the user
            message is invalid for detection, or detection returns
            an unsupported language.
        """
        policy = world.language_policy

        if not isinstance(policy, LanguagePolicy):
            raise ValueError(
                "World language policy is required."
            )

        if (
            policy.mode
            == LanguagePolicy.TARGET_LANGUAGE
        ):
            return self._resolve_target_language(
                policy
            )

        if (
            policy.mode
            == LanguagePolicy.MIRROR_USER
        ):
            return self._resolve_user_language(
                policy=policy,
                user_message=user_message,
                language_detector=language_detector,
            )

        raise ValueError(
            f"Unsupported language policy mode: "
            f"{policy.mode}"
        )

    @staticmethod
    def _resolve_target_language(
        policy: LanguagePolicy,
    ) -> str:
        target_language = policy.target_language

        if not isinstance(
            target_language,
            str,
        ):
            raise ValueError(
                "Target language must be a string."
            )

        normalized_language = (
            target_language.strip().lower()
        )

        if not normalized_language:
            raise ValueError(
                "Target language cannot be empty."
            )

        return normalized_language

    @staticmethod
    def _resolve_user_language(
        *,
        policy: LanguagePolicy,
        user_message: str,
        language_detector: LanguageDetector,
    ) -> str:
        if not isinstance(
            user_message,
            str,
        ):
            raise ValueError(
                "User message must be a string."
            )

        if not user_message.strip():
            raise ValueError(
                "User message cannot be empty."
            )

        detected_language = language_detector.detect(
            user_message
        )

        if not isinstance(
            detected_language,
            str,
        ):
            raise ValueError(
                "Detected language must be a string."
            )

        normalized_language = (
            detected_language.strip().lower()
        )

        if not normalized_language:
            raise ValueError(
                "Detected language cannot be empty."
            )

        supported_languages = {
            language.strip().lower()
            for language
            in policy.supported_languages
            if isinstance(language, str)
            and language.strip()
        }

        if normalized_language not in supported_languages:
            raise ValueError(
                "Detected language is not supported "
                "by the active World: "
                f"{normalized_language}"
            )

        return normalized_language