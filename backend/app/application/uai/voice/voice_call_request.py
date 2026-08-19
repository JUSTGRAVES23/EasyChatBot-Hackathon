"""
Voice Call Request DTO.

Represents a request to start
a character voice interaction.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallRequest:
    """
    Request data required to prepare
    a voice call.
    """

    learner_id: str

    world_id: str

    character_id: str

    language_code: str


    def __post_init__(self) -> None:

        if not self.learner_id.strip():
            raise ValueError(
                "learner_id cannot be empty."
            )

        if not self.world_id.strip():
            raise ValueError(
                "world_id cannot be empty."
            )

        if not self.character_id.strip():
            raise ValueError(
                "character_id cannot be empty."
            )

        if not self.language_code.strip():
            raise ValueError(
                "language_code cannot be empty."
            )