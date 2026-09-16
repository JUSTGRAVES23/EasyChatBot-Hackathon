"""
Voice Room Infrastructure Adapter.

Infrastructure boundary for voice rooms.

Responsibilities:
- Prepare room configuration.
- Abstract voice room provider details.

Does NOT:
- Manage learner logic.
- Execute AI.
- Persist sessions.
- Handle HTTP.
"""

from __future__ import annotations


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)



class VoiceRoomAdapter:
    """
    Provider-independent voice room adapter.

    Beta implementation:
    - Generates room metadata only.
    - Real provider integration later.
    """



    def create_room_configuration(
        self,
        *,
        context: VoiceCallExecutionContext,
    ) -> dict:
        """
        Create room configuration.
        """


        return {
            "room_name": (
                context.room.room_id
            ),
            "participants": [
                participant.participant_id
                for participant
                in context.room.participants
            ],
            "provider": "livekit",
        }
