"""
World Context.

Represents the active learning World for an AI interaction.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.uai.context.language_policy import (
    LanguagePolicy,
)


@dataclass(
    frozen=True,
    slots=True,
)
class WorldContext:
    """
    Immutable World interaction context.

    Language-learning Worlds have a target language.

    Domain Worlds may instead use mirror_user language behaviour.
    """

    world_id: str

    name: str

    language_code: str | None = None

    world_type: str = "language"

    learning_domain: str = "language_learning"

    language_policy: LanguagePolicy | None = None

    available_characters: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """
        Validate World context.
        """

        if not isinstance(self.world_id, str) or not self.world_id.strip():
            raise ValueError(
                "world_id cannot be empty."
            )

        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "world name cannot be empty."
            )

        if not isinstance(self.world_type, str) or not self.world_type.strip():
            raise ValueError(
                "world_type cannot be empty."
            )

        if (
            not isinstance(self.learning_domain, str)
            or not self.learning_domain.strip()
        ):
            raise ValueError(
                "learning_domain cannot be empty."
            )

        if self.language_code is not None:
            if not isinstance(self.language_code, str):
                raise ValueError(
                    "language_code must be a string or None."
                )

            if not self.language_code.strip():
                raise ValueError(
                    "language_code cannot be empty when provided."
                )

        if self.language_policy is not None:
            if not isinstance(
                self.language_policy,
                LanguagePolicy,
            ):
                raise ValueError(
                    "language_policy must be a LanguagePolicy."
                )