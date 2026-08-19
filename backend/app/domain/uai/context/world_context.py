"""
World Context.

Represents the active learning world
for an AI interaction.

Examples:

- French World
- Spanish World
- Business French World

The world determines:
- language
- learning environment
- available experience rules
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class WorldContext:
    """
    Immutable learning world context.
    """

    world_id: str

    name: str

    language_code: str

    available_characters: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """
        Validate world context.
        """

        if not self.world_id.strip():
            raise ValueError(
                "world_id cannot be empty."
            )

        if not self.name.strip():
            raise ValueError(
                "world name cannot be empty."
            )

        if not self.language_code.strip():
            raise ValueError(
                "language_code cannot be empty."
            )