"""
Learner Context.

Represents learner information required
for AI interaction.

This object does not handle:
- authentication
- user accounts
- payments
- persistence

It only provides learning context.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class LearnerContext:
    """
    Immutable learner context.
    """

    learner_id: str

    level: str | None = None

    native_language: str | None = None

    learning_goals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """
        Validate learner context.
        """

        if not self.learner_id.strip():
            raise ValueError(
                "learner_id cannot be empty."
            )

        if self.level is not None:
            if not self.level.strip():
                raise ValueError(
                    "level cannot be blank."
                )

        if self.native_language is not None:
            if not self.native_language.strip():
                raise ValueError(
                    "native_language cannot be blank."
                )