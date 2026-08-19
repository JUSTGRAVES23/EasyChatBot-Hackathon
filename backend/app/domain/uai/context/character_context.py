"""
Character Context.

Represents the selected AI character
for one interaction.

The character remains separate from:
- AI execution
- providers
- infrastructure
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class CharacterContext:
    """
    Immutable character interaction context.
    """

    character_id: str

    name: str

    personality_reference: str

    teaching_style: str

    premium_required: bool = False

    def __post_init__(self) -> None:
        """
        Validate character context.
        """

        if not self.character_id.strip():
            raise ValueError(
                "character_id cannot be empty."
            )

        if not self.name.strip():
            raise ValueError(
                "character name cannot be empty."
            )

        if not self.personality_reference.strip():
            raise ValueError(
                "personality_reference cannot be empty."
            )