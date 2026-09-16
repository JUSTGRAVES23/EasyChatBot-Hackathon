"""
Voice Character Agent.

Runtime coordinator for AI character voice sessions.

Responsibilities:
- Hold interaction context.
- Coordinate conversation turns.
- Apply character identity.

Does NOT:
- Connect to LiveKit.
- Perform speech recognition.
- Generate audio.
- Call providers directly.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCharacterAgent:
    """
    AI character voice runtime.

    Provider independent.
    """

    context: InteractionContext


    def get_character_id(
        self,
    ) -> str:
        """
        Return active character.
        """

        return (
            self.context
            .character
            .character_id
        )


    def get_language_code(
        self,
    ) -> str:
        """
        Return interaction language.
        """

        return (
            self.context
            .world
            .language_code
        )
