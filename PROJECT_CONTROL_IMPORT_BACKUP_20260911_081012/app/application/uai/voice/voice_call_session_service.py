"""
Voice Call Session Service.

Application service responsible for
creating execution sessions linked to
persistent voice calls.

Responsibilities:
- Create runtime voice call sessions.
- Link VoiceCall identity with execution.
- Retrieve existing voice call sessions.
- Preserve separation between:
    VoiceCall
    VoiceCallSession

Does NOT:
- Handle HTTP.
- Manage LiveKit.
- Generate tokens.
- Execute AI providers.
- Persist directly.
"""

from __future__ import annotations


from dataclasses import dataclass


from app.domain.uai.voice.voice_call import (
    VoiceCall,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallSessionService:
    """
    Creates execution sessions
    from persistent voice calls.
    """



    def create_session(
        self,
        *,
        voice_call: VoiceCall,
    ) -> VoiceCallSession:
        """
        Create a runtime execution session.

        The persistent VoiceCall ID remains
        the source identity.
        """


        return VoiceCallSession(
            session_id=(
                f"{voice_call.id}-session"
            ),
            learner_id=voice_call.learner_id,
            character_id=voice_call.character_id,
            world_id=voice_call.world_id,
            language_code=voice_call.language_code,
            state=VoiceCallState.READY,
        )



    def reconnect_session(
        self,
        *,
        voice_call: VoiceCall,
    ) -> VoiceCallSession:
        """
        Recreate execution session for
        an existing voice call.

        The VoiceCall identity remains
        unchanged.
        """


        if voice_call.state not in {
            VoiceCallState.ACTIVE,
            VoiceCallState.DISCONNECTED,
            VoiceCallState.RECONNECTABLE,
        }:
            raise ValueError(
                "Voice call cannot reconnect "
                "from current state."
            )


        return VoiceCallSession(
            session_id=(
                f"{voice_call.id}-reconnect"
            ),
            learner_id=voice_call.learner_id,
            character_id=voice_call.character_id,
            world_id=voice_call.world_id,
            language_code=voice_call.language_code,
            state=VoiceCallState.READY,
        )



__all__ = [
    "VoiceCallSessionService",
]
