"""
Voice Call Session Domain Model.

Represents a prepared voice interaction.

Does NOT:
- connect providers;
- manage LiveKit;
- execute AI.

It only represents validated
voice call state.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallSession:
    """
    Immutable voice call session.
    """

    session_id: str

    learner_id: str

    character_id: str

    world_id: str

    language_code: str

    state: VoiceCallState = (
        VoiceCallState.CREATED
    )


    def __post_init__(self) -> None:
        """
        Validate session.
        """

        if not self.session_id.strip():
            raise ValueError(
                "session_id cannot be empty."
            )


        if not self.learner_id.strip():
            raise ValueError(
                "learner_id cannot be empty."
            )


        if not self.character_id.strip():
            raise ValueError(
                "character_id cannot be empty."
            )


        if not self.world_id.strip():
            raise ValueError(
                "world_id cannot be empty."
            )


        if not self.language_code.strip():
            raise ValueError(
                "language_code cannot be empty."
            )


    def is_active(self) -> bool:
        """
        Return whether call is active.
        """

        return (
            self.state
            ==
            VoiceCallState.ACTIVE
        )


    def is_finished(self) -> bool:
        """
        Return whether call finished.
        """

        return self.state in {
            VoiceCallState.ENDED,
            VoiceCallState.FAILED,
        }
