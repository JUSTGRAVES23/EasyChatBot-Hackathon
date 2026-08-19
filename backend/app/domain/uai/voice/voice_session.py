"""
Voice Session Domain Model.

Represents one character voice interaction.

Does NOT:
- Connect to LiveKit.
- Generate tokens.
- Execute AI.
- Handle audio.

It is only the domain state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(
    frozen=True,
    slots=True,
)
class VoiceSession:
    """
    Immutable voice session state.
    """

    session_id: str

    room_name: str

    character_id: str

    language_code: str

    status: str = "created"


    def __post_init__(self) -> None:
        """
        Validate session state.
        """

        if not self.session_id.strip():
            raise ValueError(
                "session_id cannot be empty."
            )

        if not self.room_name.strip():
            raise ValueError(
                "room_name cannot be empty."
            )

        if not self.character_id.strip():
            raise ValueError(
                "character_id cannot be empty."
            )

        if not self.language_code.strip():
            raise ValueError(
                "language_code cannot be empty."
            )