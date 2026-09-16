"""
Voice Character Session Service.

Application service responsible for
creating character voice sessions.

Responsibilities:
- Coordinate character runtime.
- Coordinate speech runtime.
- Create domain voice session.
- Request LiveKit room configuration.

Does NOT:
- Call speech providers directly.
- Manage LiveKit directly.
- Store configuration.
"""

from __future__ import annotations


from dataclasses import dataclass
from uuid import uuid4


from app.ai_runtime.voice.voice_character_runtime import (
    VoiceCharacterRuntime,
)


from app.ai_runtime.voice.voice_speech_runtime import (
    VoiceSpeechRuntime,
)


from app.domain.uai.context.interaction_context import (
    InteractionContext,
)


from app.domain.uai.voice.voice_session import (
    VoiceSession,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCharacterSessionService:
    """
    Creates voice sessions for AI characters.
    """

    livekit_adapter: object

    speech_runtime: VoiceSpeechRuntime



    def create_session(
        self,
        *,
        context: InteractionContext,
    ) -> VoiceSession:
        """
        Create a character voice session.
        """


        character_runtime = (
            VoiceCharacterRuntime(
                context=context,
                speech_runtime=(
                    self.speech_runtime
                ),
            )
        )


        character_id = (
            character_runtime
            .character_id()
        )


        session = VoiceSession(
            session_id=str(
                uuid4()
            ),
            room_name=(
                f"{character_id}-voice-room"
            ),
            character_id=character_id,
            language_code=(
                context.voice.language_code
            ),
        )


        self.livekit_adapter.create_room_configuration(
            session=session,
        )


        return session
