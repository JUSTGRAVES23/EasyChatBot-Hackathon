"""
World language policy.

Defines how a World determines the language used for interaction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LanguagePolicy:
    """
    Immutable language interaction policy.

    Modes
    -----
    target_language:
        The World has one configured target language.

    mirror_user:
        The World responds using the language detected from the
        user's message, subject to the configured supported languages.
    """

    mode: str
    target_language: str | None = None
    supported_languages: tuple[str, ...] = ()

    TARGET_LANGUAGE = "target_language"
    MIRROR_USER = "mirror_user"

    def __post_init__(self) -> None:
        if self.mode not in (
            self.TARGET_LANGUAGE,
            self.MIRROR_USER,
        ):
            raise ValueError(
                f"Unsupported language policy mode: {self.mode}"
            )

        if self.mode == self.TARGET_LANGUAGE:
            if not self.target_language:
                raise ValueError(
                    "target_language is required for target_language mode."
                )

            if not self.target_language.strip():
                raise ValueError(
                    "target_language cannot be empty."
                )

        if self.mode == self.MIRROR_USER:
            if not self.supported_languages:
                raise ValueError(
                    "supported_languages are required for mirror_user mode."
                )

            if any(
                not isinstance(language, str)
                or not language.strip()
                for language in self.supported_languages
            ):
                raise ValueError(
                    "supported_languages must contain non-empty strings."
                )