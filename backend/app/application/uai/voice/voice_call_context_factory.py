"""
Voice Call Context Factory.

Application factory responsible for
creating voice execution contexts.

Responsibilities:
- Convert voice call requests into
  domain execution context.
- Create voice sessions.
- Create room participants.
- Build validated execution boundary.

Does NOT:
- Handle HTTP.
- Execute runtime.
- Connect LiveKit.
- Select providers.
- Persist data.
"""

from __future__ import annotations


from dataclasses import dataclass


from backend.app.application.uai.voice.voice_call_request import (
    VoiceCallRequest,
)


from app.domain.uai.voice.voice_call_execution_context import (
    VoiceCallExecutionContext,
)


from app.domain.uai.voice.voice_call_session import (
    VoiceCallSession,
)


from app.domain.uai.voice.voice_call_state import (
    VoiceCallState,
)


from app.domain.uai.voice.voice_call_room import (
    VoiceCallRoom,
)


from app.domain.uai.voice.voice_call_participant import (
    VoiceCallParticipant,
    VoiceParticipantRole,
)



@dataclass(
    frozen=True,
    slots=True,
)
class VoiceCallContextFactory:
    """
    Creates voice execution contexts.
    """



    def create(
        self,
        *,
        request: VoiceCallRequest,
    ) -> VoiceCallExecutionContext:
        """
        Create execution context.

        Lifecycle starts:

            READY
              |
              â†“
          Runtime ACTIVE
        """


        session = VoiceCallSession(
            session_id=(
                f"{request.character_id}-"
                f"{request.learner_id}"
            ),
            learner_id=request.learner_id,
            character_id=request.character_id,
            world_id=request.world_id,
            language_code=request.language_code,
            state=VoiceCallState.READY,
        )


        room = VoiceCallRoom(
            room_id=session.session_id,
            participants=(
                VoiceCallParticipant(
                    participant_id=request.learner_id,
                    role=(
                        VoiceParticipantRole.LEARNER
                    ),
                    display_name="Learner",
                ),
                VoiceCallParticipant(
                    participant_id=request.character_id,
                    role=(
                        VoiceParticipantRole.CHARACTER
                    ),
                    display_name=(
                        request.character_id
                    ),
                ),
            ),
        )


        return VoiceCallExecutionContext(
            session=session,
            room=room,
        )



__all__ = [
    "VoiceCallContextFactory",
]
